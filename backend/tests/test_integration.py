"""TEST-003: hành vi chỉ kiểm chứng được với Mongo/Redis thật.

Các test ở đây nhắm vào thứ mà test với mock không bao giờ bắt được:

- Transaction chỉ chạy trên **replica set**. Đây là điều kiện tiên quyết cho
  `PROD-004` (xoá POI cascade không dữ liệu mồ côi), nên phải xác nhận sớm
  thay vì để tới Phase 14 mới phát hiện.
- Ràng buộc unique `(poi_id, lang)` phải **thật sự** chặn ghi trùng.
- `$geoNear` chỉ chạy được khi đã có index `2dsphere`; hỏng index thì phải rơi
  về Haversine với kết quả tương đương.
- TTL index phải thật sự dọn bản ghi hết hạn.
- Rate limit phải **chia sẻ trạng thái** giữa các client.

Cách chạy:

    docker compose -f docker-compose.test.yml up -d --wait
    cd backend
    $env:MONGODB_URI="mongodb://localhost:27018/?directConnection=true"
    $env:REDIS_URL="redis://localhost:6380"
    pytest -m integration

Test tự bỏ qua nếu Mongo đang chạy không phải replica set, để `pytest` thường
vẫn xanh trên máy dev chỉ có Mongo standalone.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pymongo import MongoClient

from app.config import settings

pytestmark = pytest.mark.integration

DB_TEN = "amds_integration"


def client() -> MongoClient:
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)


def db():
    return client()[DB_TEN]


def co_replica_set() -> bool:
    try:
        return client().admin.command("hello").get("setName") is not None
    except Exception:
        return False


requires_replica_set = pytest.mark.skipif(
    not co_replica_set(),
    reason="Cần Mongo replica set (docker compose -f docker-compose.test.yml up -d)",
)


def xoa_sach() -> None:
    for ten in db().list_collection_names():
        db()[ten].delete_many({})


async def xoa_sach_async(adb) -> None:
    """Bản async: Motor trả Future nên không dùng chung helper sync được."""
    for ten in await adb.list_collection_names():
        await adb[ten].delete_many({})


def adb():
    """Database Motor cho các hàm async của app."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(settings.mongodb_uri)[DB_TEN]


# --- Transaction: điều kiện tiên quyết cho PROD-004 ---


@requires_replica_set
def test_transaction_commit_ghi_ca_hai_ve() -> None:
    xoa_sach()
    # Session chỉ dùng được với đúng client đã tạo ra nó, nên giữ một biến `d`.
    c = client()
    d = c[DB_TEN]
    with c.start_session() as phien:
        with phien.start_transaction():
            d["pois"].insert_one({"_id": 1, "name": "A"}, session=phien)
            d["deleted_pois"].insert_one({"_id": 1, "poi_id": 1}, session=phien)
    assert d["pois"].count_documents({}) == 1
    assert d["deleted_pois"].count_documents({}) == 1


@requires_replica_set
def test_transaction_rollback_khong_de_du_lieu_noi_bo() -> None:
    """Ném lỗi giữa chừng thì rollback sạch — đây là điều PROD-004 cần."""
    xoa_sach()
    c = client()
    d = c[DB_TEN]
    with pytest.raises(RuntimeError):
        with c.start_session() as phien:
            with phien.start_transaction():
                d["pois"].insert_one({"_id": 2, "name": "B"}, session=phien)
                d["audit_logs"].insert_one({"_id": 2, "action": "x"}, session=phien)
                raise RuntimeError("hỏng giữa chừng")
    assert d["pois"].count_documents({}) == 0
    assert d["audit_logs"].count_documents({}) == 0


@requires_replica_set
def test_transaction_rollback_khi_trung_khoa() -> None:
    """Vi phạm unique index giữa transaction phải rollback, không giữ dữ liệu rác."""
    xoa_sach()
    c = client()
    d = c[DB_TEN]
    d["poi_localizations"].insert_one({"_id": "d", "poi_id": "p", "lang": "vi"})
    d["poi_localizations"].create_index([("poi_id", 1), ("lang", 1)], unique=True)
    with pytest.raises(Exception):  # noqa: B017 - DuplicateKeyError hay OperationFailure đều hợp lệ
        with c.start_session() as phien:
            with phien.start_transaction():
                d["poi_localizations"].insert_one({"_id": "x", "poi_id": "p", "lang": "ja"}, session=phien)
                d["poi_localizations"].insert_one(
                    {"_id": "y", "poi_id": "p", "lang": "vi"}, session=phien
                )
    assert d["poi_localizations"].count_documents({}) == 1


# --- Ràng buộc unique thật sự chặn ghi trùng ---


def test_unique_poi_lang_chan_ghi_trung() -> None:
    from pymongo.errors import DuplicateKeyError

    from app.services.localization import dam_bao_index

    async def chay() -> None:
        a = adb()
        await xoa_sach_async(a)
        await dam_bao_index(a)
        oid = uuid.uuid4().hex[:24]
        await a["poi_localizations"].insert_one({"poi_id": oid, "lang": "vi", "name": "A"})
        with pytest.raises(DuplicateKeyError):
            await a["poi_localizations"].insert_one({"poi_id": oid, "lang": "vi", "name": "B"})
        # Cùng POI nhưng khác ngôn ngữ thì phải vào được.
        await a["poi_localizations"].insert_one({"poi_id": oid, "lang": "en", "name": "B"})
        assert await a["poi_localizations"].count_documents({"poi_id": oid}) == 2

    asyncio.run(chay())


# --- $geoNear chỉ chạy khi có index 2dsphere, hỏng thì fallback ---


def test_geo_near_dung_index_khong_thi_fallback() -> None:
    from app.routers.geo import dam_bao_geo, gan_khoang_cach

    async def chay() -> tuple[int, int]:
        a = adb()
        await xoa_sach_async(a)
        await a["pois"].insert_many(
            [
                {"name": "Gan", "lat": 10.7569, "lng": 106.7641},
                {"name": "Xa", "lat": 10.9000, "lng": 106.9000},
            ]
        )
        await dam_bao_geo(a)
        co_index = await gan_khoang_cach(a, 10.7569, 106.7641, 1500, "vi")

        await a["pois"].drop_index("location_2dsphere")
        het_index = await gan_khoang_cach(a, 10.7569, 106.7641, 1500, "vi")
        return len(co_index), len(het_index)

    assert asyncio.run(chay()) == (1, 1)


# --- TTL index thật sự dọn bản ghi hết hạn ---


def test_ttl_index_don_ban_ghi_het_han() -> None:
    from app.services.ratelimit import dam_bao_index_ratelimit

    async def chay() -> int:
        a = adb()
        await xoa_sach_async(a)
        await dam_bao_index_ratelimit(a)
        await a["rate_limits"].insert_one({"het_han": datetime.now(UTC) - timedelta(seconds=5)})
        await a["rate_limits"].insert_one({"het_han": datetime.now(UTC) + timedelta(hours=1)})
        for _ in range(70):
            await asyncio.sleep(1)
            if await a["rate_limits"].count_documents({}) == 1:
                break
        return await a["rate_limits"].count_documents({})

    assert asyncio.run(chay()) == 1


# --- Rate limit phải chia sẻ trạng thái giữa các client ---


def test_rate_limit_chia_sea_trang_thai() -> None:
    """Rate limit trong bộ nhớ sẽ sai khi nhiều tiến trình; Mongo TTL thì đúng."""
    from app.services.ratelimit import cho_phep

    async def chay() -> tuple[int, bool]:
        a = adb()
        await xoa_sach_async(a)
        lan_dung = 0
        for _ in range(5):
            ok, _cho = await cho_phep(a, "khoa:chung", "duong-dan:chung", 5, 10)
            if ok:
                lan_dung += 1
        # Client khác dùng cùng khoa vẫn phải thấy đã đủ lượt.
        ok_sau, _ = await cho_phep(a, "khoa:chung", "duong-dan:chung", 5, 10)
        return lan_dung, ok_sau

    lan_dung, ok_sau = asyncio.run(chay())
    assert lan_dung == 5
    assert ok_sau is False


# --- Redis: hiện diện đếm thiết bị, không đếm tab ---


def test_redis_presence_dem_thiet_bi() -> None:
    from app.services.presence import CUA_SO_GIOY, dem_online, heartbeat, xoa_het

    async def chay() -> tuple[int | None, int | None, int | None]:
        await xoa_het()
        for _ in range(4):
            await heartbeat(f"thiet-bi-{uuid.uuid4().hex[:12]}")
        a = await dem_online()
        await heartbeat(f"thiet-bi-{uuid.uuid4().hex[:12]}")
        b = await dem_online()
        await xoa_het()
        c = await dem_online()
        return a, b, c

    a, b, sau = asyncio.run(chay())
    if a is None:
        pytest.skip("Redis đang tắt — presence fail-open đúng như thiết kế")
    assert a == 4
    assert b == 5
    assert sau == 0
    assert CUA_SO_GIOY == 300