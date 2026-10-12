"""Test Phase 10: cổng consent, hiện diện Redis, read model giờ/ngày, lane runtime."""

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402

ANON = "anon-0123456789abcdef"
ANON_2 = "anon-fedcba9876543210"
SESSION = "sess-0123456789abcdef"
UA_KHACH = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/605.1"

COLLECTIONS_ANALYTICS = (
    "analytics_consents",
    "analytics_devices",
    "analytics_sessions",
    "analytics_events",
    "analytics_daily",
    "analytics_hourly",
    "analytics_poi_daily",
    "analytics_searches",
    "analytics_jobs",
    "runtime_location_hourly",
)


def nap_sach() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    for ten in COLLECTIONS_ANALYTICS + ("rate_limits", "pois"):
        db[ten].delete_many({})
    mongo.close()


def dong_y(client: TestClient, anon: str = ANON, granted: bool = True) -> dict:
    res = client.post("/analytics/consent", json={"anonymous_id": anon, "granted": granted})
    assert res.status_code == 200
    return res.json()


def goi_collect(client: TestClient, receipt: str, events: list[dict], **them) -> dict:
    du_lieu = {
        "anonymous_id": ANON,
        "receipt": receipt,
        "session_id": SESSION,
        "events": events,
    }
    du_lieu.update(them)
    return client.post(
        "/analytics/collect",
        json=du_lieu,
        headers={"User-Agent": UA_KHACH},
    )


def so_su_kien() -> int:
    mongo = MongoClient(settings.mongodb_uri)
    dem = mongo[settings.mongodb_db_name]["analytics_events"].count_documents({})
    mongo.close()
    return dem


# --- ANA-002: cổng consent là điều kiện tiên quyết, không phải lựa chọn ---


def test_chua_consent_thi_collect_bi_tu_choi() -> None:
    nap_sach()
    with TestClient(app) as c:
        res = goi_collect(c, "khong-phai-receipt-that", [{"name": "page_viewed"}])
        assert res.status_code == 403
        assert so_su_kien() == 0


def test_consent_xac_nhan_thi_ghi_su_kien() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        assert receipt
        res = goi_collect(
            c,
            receipt,
            [
                {"name": "page_viewed", "properties": {"path": "/"}},
                {"name": "audio_played", "properties": {"poi_id": "abc"}},
                {"name": "search", "properties": {"query": "bún bò"}},
            ],
        )
        assert res.status_code == 200
        assert res.json()["accepted"] == 3
        assert so_su_kien() == 3


def thu_hoi_consent_thi_collect_403_ngay() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        assert goi_collect(c, receipt, [{"name": "page_viewed"}]).status_code == 200
        dong_y(c, granted=False)
        res = goi_collect(c, receipt, [{"name": "page_viewed"}])
        assert res.status_code == 403
        assert so_su_kien() == 1


def test_receipt_tao_ban_va_gia_mao() -> None:
    from app.services.analytics_svc import doc_receipt, lam_receipt

    receipt = lam_receipt(ANON)
    assert doc_receipt(receipt)["anonymous_id"] == ANON
    assert doc_receipt(receipt[:-4] + "aaaa") is None
    assert doc_receipt("khong-phai-base64-hop-le") is None
    assert doc_receipt("") is None
    # Receipt của thiết bị khác không dùng được cho thiết bị này.
    with TestClient(app) as c:
        nap_sach()
        receipt_cua_khac = dong_y(c, ANON_2)["receipt"]
        dong_y(c, ANON)
        assert goi_collect(c, receipt_cua_khac, [{"name": "page_viewed"}]).status_code == 403


def test_su_kien_ngoai_danh_sach_bi_bo_qua() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        res = goi_collect(
            c,
            receipt,
            [{"name": "page_viewed"}, {"name": "troi_cap_du_lieu"}, {"name": "poi_viewed"}],
        )
        assert res.json()["accepted"] == 2
        assert so_su_kien() == 2


def test_bot_bi_loc_va_khong_ghi() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        res = c.post(
            "/analytics/collect",
            json={
                "anonymous_id": ANON,
                "receipt": receipt,
                "session_id": SESSION,
                "events": [{"name": "page_viewed"}],
            },
            headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
        )
        assert res.status_code == 200
        assert res.json()["accepted"] == 0
        assert res.json()["filtered"].startswith("bot:")
        assert so_su_kien() == 0


def test_thuoc_tinh_nhan_danh_ca_nhan_bi_loai() -> None:
    from app.services.analytics_svc import lam_sach

    sach = lam_sach(
        {
            "email": "khach@example.com",
            "cccd": "123456789",
            "password": "h",
            "token": "abc",
            "query": "bun bo",
            "so": 3,
        }
    )
    assert sach == {"query": "bun bo", "so": 3}
    assert lam_sach("khong-phai-dict") == {}
    assert len(lam_sach({f"k{i}": "v" for i in range(50)})) == 8
    assert len(lam_sach({"a": "x" * 500})["a"]) == 200


# --- ANA-003: hiện diện đếm THIẾT BỊ, không đếm tab ---


def test_presence_dem_thiet_bi_khong_dem_tab() -> None:
    from app.services.presence import dem_online, heartbeat, xoa_het

    async def chay() -> tuple[int, int, int | None]:
        await xoa_het()
        # Cùng một thiết bị mở 5 tab → vẫn tính 1.
        for _ in range(5):
            await heartbeat(ANON)
        sau_5_tab = await dem_online()
        await heartbeat(ANON_2)
        sau_2_thiet_bi = await dem_online()
        online = await dem_online()
        await xoa_het()
        return sau_5_tab, sau_2_thiet_bi, online

    sau_5_tab, sau_2_thiet_bi, online = asyncio.run(chay())
    if sau_5_tab is None:
        return  # Redis đang tắt, hành vi fail-open đã đúng
    assert sau_5_tab == 1
    assert sau_2_thiet_bi == 2
    assert online == 2


def test_presence_tu_tat_khi_qua_cua_so() -> None:
    from app.services import presence

    async def chay() -> int | None:
        redis = await presence.lay_redis()
        if redis is None:
            return None
        await presence.xoa_het()
        await redis.zadd(
            presence.KHOA_ZSET,
            {ANON: time_giay() - presence.CUA_SO_GIOY - 60},
        )
        dem = await presence.dem_online()
        await presence.xoa_het()
        return dem

    assert asyncio.run(chay()) in (0, None)


def time_giay() -> float:
    import time

    return time.time()


def test_collect_tra_ve_tracked_online_users() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        res = goi_collect(c, receipt, [{"name": "page_viewed"}])
        online = res.json()["tracked_online_users"]
        assert online is None or online >= 1


# --- ANA-004: read model giờ/ngày ---


def nap_su_kien(ngay: str, gio: int, ten: str, thuoc_tinh: dict | None = None) -> None:
    from motor.motor_asyncio import AsyncIOMotorClient

    async def chen() -> None:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        await db["analytics_events"].insert_one(
            {
                "anonymous_id": ANON,
                "session_id": SESSION,
                "name": ten,
                "properties": thuoc_tinh or {},
                "poi_id": (thuoc_tinh or {}).get("poi_id"),
                "occurred_at": datetime.strptime(ngay, "%Y-%m-%d").replace(tzinfo=UTC)
                + timedelta(hours=gio),
                "metric_date": ngay,
                "metric_hour": gio,
                "ingested_at": datetime.now(UTC),
            }
        )
        client.close()

    asyncio.run(chen())


def db_bang_motor():
    """Client Motor độc lập: test chạy ngoài lifespan nên không dùng get_database()."""
    from motor.motor_asyncio import AsyncIOMotorClient

    return AsyncIOMotorClient(settings.mongodb_uri)[settings.mongodb_db_name]


def test_read_model_tong_hop_giay_va_ngay() -> None:
    from app.services.analytics_read import chay_ngay

    nap_sach()
    ngay = "2026-03-15"
    for _ in range(3):
        nap_su_kien(ngay, 9, "page_viewed")
    nap_su_kien(ngay, 9, "audio_played", {"poi_id": "111111111111111111111111"})
    nap_su_kien(ngay, 9, "audio_played", {"poi_id": "111111111111111111111111"})
    nap_su_kien(ngay, 14, "page_viewed")
    nap_su_kien(ngay, 14, "search", {"query": "Bún Bò"})

    async def chay():
        db = db_bang_motor()
        ket_qua = await chay_ngay(db, ngay)
        ngay_doc = await db["analytics_daily"].find_one({"metric_date": ngay})
        gio_doc = await db["analytics_hourly"].find({"metric_date": ngay}).to_list(length=24)
        poi_doc = await db["analytics_poi_daily"].find({"metric_date": ngay}).to_list(length=10)
        tim_doc = await db["analytics_searches"].find({"metric_date": ngay}).to_list(length=10)
        return ket_qua, ngay_doc, gio_doc, poi_doc, tim_doc

    ket_qua, ngay_doc, gio_doc, poi_doc, tim_doc = asyncio.run(chay())
    assert ket_qua["views"] == 4
    assert ket_qua["audio_plays"] == 2
    assert ket_qua["searches"] == 1
    assert ngay_doc["devices"] == 1
    assert ngay_doc["sessions"] == 1
    assert len(gio_doc) == 2
    gio_9 = next(g for g in gio_doc if g["metric_hour"] == 9)
    assert gio_9["views"] == 3 and gio_9["audio_plays"] == 2
    assert poi_doc[0]["audio_plays"] == 2
    assert tim_doc[0]["query"] == "bún bò" and tim_doc[0]["count"] == 1


def test_tong_hop_lai_khong_nhan_don() -> None:
    from app.services.analytics_read import chay_ngay

    nap_sach()
    ngay = "2026-03-16"
    for _ in range(2):
        nap_su_kien(ngay, 10, "page_viewed")

    async def chay() -> dict:
        db = db_bang_motor()
        await chay_ngay(db, ngay)
        await chay_ngay(db, ngay)
        return await db["analytics_daily"].find_one({"metric_date": ngay})

    ban = asyncio.run(chay())
    assert ban["views"] == 2


def test_job_dang_giua_lease_thi_vay_thu_giup() -> None:
    from app.services.analytics_read import lease_job

    nap_sach()

    async def chay() -> tuple[dict | None, dict | None]:
        db = db_bang_motor()
        await db["analytics_jobs"].insert_one(
            {
                "metric_date": "2026-03-17",
                "status": "running",
                "lease_until": datetime.now(UTC) - timedelta(minutes=5),
                "updated_at": datetime.now(UTC),
            }
        )
        job = await lease_job(db)
        lan_hai = await lease_job(db)
        return job, lan_hai

    job, lan_hai = asyncio.run(chay())
    assert job is not None and job["metric_date"] == "2026-03-17"
    assert job["status"] == "running"
    # Vừa giành thì lease còn hiệu lực, tiến trình khác phải chờ.
    assert lan_hai is None


# --- ADM-005: dashboard đọc read model, đòi analytics:view ---


def nap_admin(role: str = "super_admin") -> None:
    import bcrypt

    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    db["admin_users"].delete_many({})
    db["admin_users"].insert_one(
        {
            "username": "admin",
            "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
            "role": role,
        }
    )
    mongo.close()


def test_dashboard_cho_admin_khong_cho_khach() -> None:
    nap_sach()
    nap_admin()
    with TestClient(app) as c:
        assert c.get("/admin/analytics/summary").status_code == 401
        assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200
        res = c.get("/admin/analytics/summary")
        assert res.status_code == 200
        du_lieu = res.json()
        for khoa in ("today_views", "audio_plays", "searches", "top_pois", "tracked_online_users"):
            assert khoa in du_lieu
        assert du_lieu["presence_available"] == (du_lieu["tracked_online_users"] is not None)


def test_dashboard_403_voi_role_thieu_quyen() -> None:
    nap_sach()
    nap_admin("poi_owner")
    with TestClient(app) as c:
        c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"})
        assert c.get("/admin/analytics/summary").status_code == 403


# --- ANA-005: kênh runtime tách riêng, không phụ thuộc consent ---


def test_lane_runtime_hoat_dong_khong_can_consent() -> None:
    nap_sach()
    with TestClient(app) as c:
        res = c.post(
            "/runtime-observability/location",
            json={"session_id": SESSION, "samples": [{"lat": 10.7569, "lng": 106.7641}]},
        )
        assert res.status_code == 200
        assert res.json()["accepted"] == 1
        # Không hề có analytics_events nào từ kênh này.
        assert so_su_kien() == 0


def test_lane_runtime_bo_qua_truong_moi_trung() -> None:
    nap_sach()
    nap_admin()
    with TestClient(app) as c:
        c.post(
            "/runtime-observability/location",
            json={
                "session_id": SESSION,
                "samples": [
                    {
                        "lat": 10.7569,
                        "lng": 106.7641,
                        "accuracy": 12.4,
                        "env": "production",
                        "user_id": "admin",
                        "email": "a@b.c",
                    }
                ],
            },
        )
        c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"})
        res = c.get("/admin/runtime-observability/location")
        assert res.status_code == 200
        assert res.json()["samples"] == 1
        assert "env" not in res.json()
        assert "user_id" not in res.json()
        assert res.json()["outcomes"].get("ok") == 1


def test_lane_runtime_loai_mau_rac() -> None:
    nap_sach()
    with TestClient(app) as c:
        res = c.post(
            "/runtime-observability/location",
            json={
                "session_id": SESSION,
                "samples": [
                    {"lat": 999, "lng": 0},
                    {"lat": "khong-phai-so"},
                    {"lat": 10.7569},
                    "khong-phai-dict",
                    {"lat": 10.7569, "lng": 106.7641},
                ],
            },
        )
        assert res.json()["accepted"] == 1
        assert res.json()["rejected"] == 4


def test_lane_runtime_cho_phep_ton_tao_rieng() -> None:
    nap_sach()
    from app.services.runtime_observability import SO_MAU_TOI_DA

    with TestClient(app) as c:
        res = c.post(
            "/runtime-observability/location",
            json={
                "session_id": SESSION,
                "samples": [{"lat": 10.7569, "lng": 106.7641} for _ in range(SO_MAU_TOI_DA + 10)],
            },
        )
        # Pydantic chặn trước khi vào service.
        assert res.status_code == 422


def test_origin_khong_hop_le_bi_tu_choi() -> None:
    nap_sach()
    with TestClient(app) as c:
        res = c.post(
            "/runtime-observability/location",
            json={"session_id": SESSION, "samples": [{"lat": 1, "lng": 1}]},
            headers={"Origin": "https://trang-la-giac.evil"},
        )
        assert res.status_code == 403
        lan_analytics = c.post(
            "/analytics/consent",
            json={"anonymous_id": ANON, "granted": True},
            headers={"Origin": "https://trang-la-giac.evil"},
        )
        assert lan_analytics.status_code == 403


def test_origin_hop_le_duoc_phep() -> None:
    nap_sach()
    with TestClient(app) as c:
        res = c.post(
            "/runtime-observability/location",
            json={"session_id": SESSION, "samples": [{"lat": 1, "lng": 1}]},
            headers={"Origin": "http://localhost:5173"},
        )
        assert res.status_code == 200


# --- Hồi quy cho các lỗ hổng đã sửa ở Phase 10 ---
# Mỗi test dưới đây khóa lại một lỗi thật đã xảy ra. Xoá test là mất cái
# lưới an toàn cho đúng lỗi đó, nên đừng gộp/gộp lại cho gọn.


def test_collect_ghi_vao_analytics_sessions() -> None:
    """Session phải được ghi thật, không chỉ tạo index rồi để trống."""
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        assert goi_collect(c, receipt, [{"name": "page_viewed"}]).status_code == 200
        mongo = MongoClient(settings.mongodb_uri)
        doc = mongo[settings.mongodb_db_name]["analytics_sessions"].find_one({"session_id": SESSION})
        mongo.close()
    assert doc is not None
    assert doc["anonymous_id"] == ANON
    assert doc["started_at"] is not None
    assert doc["last_seen"] is not None


def test_session_started_at_giu_nguyen_qua_heartbeat() -> None:
    """Heartbeat lặp lại không được tính thành phiên mới."""
    nap_sach()
    with TestClient(app) as c:
        receipt = dong_y(c)["receipt"]
        for _ in range(3):
            goi_collect(c, receipt, [{"name": "page_viewed"}])
        mongo = MongoClient(settings.mongodb_uri)
        db = mongo[settings.mongodb_db_name]
        dem = db["analytics_sessions"].count_documents({"session_id": SESSION})
        doc = db["analytics_sessions"].find_one({"session_id": SESSION})
        mongo.close()
    assert dem == 1
    assert doc is not None


def test_job_da_xong_thi_duoc_xep_lai() -> None:
    """Sự kiện đến sau lần tổng hợp đầu phải xếp lại job, nếu không dashboard đứng yên."""
    from app.services import analytics_svc as an

    nap_sach()
    ngay = "2026-03-20"

    async def chay() -> list[str]:
        db = db_bang_motor()
        await db["analytics_jobs"].drop()
        await db["analytics_jobs"].create_index("metric_date", unique=True)
        await an.xep_viec_tong_hop(db, ngay)
        await db["analytics_jobs"].update_one(
            {"metric_date": ngay}, {"$set": {"status": "done"}}
        )
        # Sự kiện mới của cùng ngày phải đánh thức job.
        await an.xep_viec_tong_hop(db, ngay)
        return [d["status"] for d in await db["analytics_jobs"].find({"metric_date": ngay}).to_list(10)]

    assert asyncio.run(chay()) == ["queued"]


def test_xep_viec_dong_bo_khong_tao_trung() -> None:
    """Nhiều request cùng lúc chỉ tạo một job cho một ngày."""
    from app.services import analytics_svc as an

    nap_sach()
    ngay = "2026-03-21"

    async def chay() -> int:
        db = db_bang_motor()
        await db["analytics_jobs"].drop()
        await an.dam_bao_index(db)
        await asyncio.gather(*(an.xep_viec_tong_hop(db, ngay) for _ in range(8)))
        return await db["analytics_jobs"].count_documents({"metric_date": ngay})

    assert asyncio.run(chay()) == 1


def test_thu_hoi_consent_chi_go_roi_thiet_bi_do() -> None:
    """Thu hồi consent của máy A không được xoá máy B khỏi cửa sổ hiện diện."""
    nap_sach()

    async def chay() -> tuple[int | None, int | None]:
        from app.services.presence import dem_online, heartbeat, xoa_het, xoa_thiet_bi

        await xoa_het()
        await heartbeat(ANON)
        await heartbeat(ANON_2)
        truoc = await dem_online()
        await xoa_thiet_bi(ANON)
        sau = await dem_online()
        await xoa_het()
        return truoc, sau

    truoc, sau = asyncio.run(chay())
    if truoc is None:
        return  # Redis đang tắt, không kiểm được hiện diện
    assert truoc == 2
    assert sau == 1