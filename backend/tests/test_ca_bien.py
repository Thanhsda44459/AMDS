"""TEST-005: bộ test ca biên — rỗng, quá dài, ký tự lạ, trùng lặp, đồng thời.

Nguyên tắc khi làm bộ này: **đằng nào phải trả lỗi cũng phải trả lỗi có kiểm
soát** (4xx), không bao giờ 500 và không bao giờ im lặng. Một endpoint sập vì
payload lạ là lỗ hổng DoS, không phải chuyện nhỏ.

Nhóm rủi ro chính được bắt ở đây:
- Input rỗng/sai kiểu → pydantic chặn ở biên.
- Chuỗi rất dài → có trần độ dài, không để dồn vào DB.
- Ký tự lạ và **toán tử `$` của MongoDB** → không được biến thành truy vấn
  (NoSQL injection, SEC-008).
- Ghi trùng → không sinh bản ghi rác.
- Ghi đồng thời → không vượt ngưỡng rate limit và không tạo bản ghi trùng.
"""

import asyncio
import threading

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402

ANON = "anon-0123456789abcdef"
ANON_2 = "anon-fedcba9876543210"
SESSION = "sess-0123456789abcdef"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/605.1"

KY_TU_LA = ["<script>alert(1)</script>", "'; DROP TABLE pois; --", "../../etc/passwd", "\x00\x01", "😀🎉", "a" * 5000]
# Toán tử Mongo: nếu lọt xuống query sẽ đổi cấu trúc truy vấn, không phải tìm kiếm.
KY_NO_SQL = [{"$ne": None}, {"$gt": ""}, {"$exists": True}, {"$regex": ".*"}, {"$where": "1==1"}]


def nap_sach() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    for ten in (
        "analytics_consents", "analytics_devices", "analytics_sessions", "analytics_events",
        "analytics_jobs", "analytics_daily", "analytics_hourly", "analytics_poi_daily",
        "analytics_searches", "runtime_location_hourly", "rate_limits", "pois",
        "admin_users", "poi_localizations", "audit_logs",
    ):
        db[ten].delete_many({})
    mongo.close()


def nap_admin() -> None:
    import bcrypt
    from pymongo import MongoClient as MC

    mongo = MC(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    db["admin_users"].delete_many({})
    db["admin_users"].insert_one(
        {"username": "admin", "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
         "role": "super_admin"}
    )
    mongo.close()


def dong_nhap(c: TestClient) -> None:
    assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def consent(c: TestClient, anon: str = ANON) -> str:
    res = c.post("/analytics/consent", json={"anonymous_id": anon, "granted": True})
    assert res.status_code == 200
    return res.json()["receipt"]


def post_collect(c: TestClient, receipt: str, events: list, **them):
    du_lieu = {"anonymous_id": ANON, "receipt": receipt, "session_id": SESSION, "events": events}
    du_lieu.update(them)
    return c.post("/analytics/collect", json=du_lieu, headers={"User-Agent": UA})


# --- Rỗng và sai kiểu ---


def test_analytics_input_rong_bi_tu_choi() -> None:
    nap_sach()
    with TestClient(app) as c:
        assert c.post("/analytics/consent", json={}).status_code == 422
        assert c.post("/analytics/consent", json={"anonymous_id": ANON}).status_code == 422
        assert c.post("/analytics/consent", json={"anonymous_id": "", "granted": True}).status_code == 422
        assert c.post("/analytics/consent", json={"anonymous_id": 123, "granted": True}).status_code == 422
        # granted thiếu hoặc sai kiểu chuỗi đều phải bị chặn, không ép true.
        assert c.post("/analytics/consent", json={"anonymous_id": ANON, "granted": "co"}).status_code == 422


def test_collect_input_rong_bi_tu_choi() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = consent(c)
        assert post_collect(c, receipt, []).status_code == 200  # lô rỗng thì hợp lệ
        assert c.post("/analytics/collect", json={"receipt": receipt, "session_id": SESSION}).status_code == 422
        assert post_collect(c, "", [{"name": "page_viewed"}]).status_code == 422
        assert post_collect(c, receipt, [{"name": ""}]).status_code == 422
        assert post_collect(c, receipt, [{"name": "page_viewed", "properties": "khong-phai-dict"}]).status_code == 422


def test_poi_input_rong_va_sai_kieu() -> None:
    nap_sach()
    nap_admin()
    with TestClient(app) as c:
        dong_nhap(c)
        assert c.post("/admin/pois", json={}).status_code == 422
        assert c.post("/admin/pois", json={"name": "X", "lat": "abc", "lng": 1}).status_code == 422
        assert c.post("/admin/pois", json={"name": "X", "lat": None, "lng": 1}).status_code == 422
        assert c.post("/admin/pois", json={"name": "X", "lat": 10.75}).status_code == 422


# --- Quá dài ---


def test_chuoi_qua_dai_bi_chan_co_tran() -> None:
    nap_sach()
    nap_admin()
    with TestClient(app) as c:
        dong_nhap(c)
        lon = "x" * 100_000
        assert c.post("/admin/pois", json={"name": lon, "lat": 10.75, "lng": 106.76}).status_code == 422
        assert c.post("/admin/pois", json={"name": "Q", "description": lon, "lat": 10.75, "lng": 106.76}).status_code == 422
        assert c.post("/analytics/consent", json={"anonymous_id": ANON, "granted": True, "x": lon}).status_code == 200
        # anonymous_id vượt 64 ký tự thì 422 chứ không cắt bừa.
        assert c.post("/analytics/consent", json={"anonymous_id": "a" * 65, "granted": True}).status_code == 422


def test_lot_su_kien_toi_han_bi_chan() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = consent(c)
        assert post_collect(c, receipt, [{"name": "page_viewed"}] * 51).status_code == 422
        assert post_collect(c, receipt, [{"name": "page_viewed"}] * 50).status_code == 200


# --- Ký tự lạ: không được sập, không được lộ stack trace ---


def test_ky_tu_la_khong_lam_sap_server() -> None:
    nap_sach()
    nap_admin()
    with TestClient(app) as c:
        dong_nhap(c)
        for ky in KY_TU_LA:
            res = c.post("/admin/pois", json={"name": ky, "description": ky, "lat": 10.75, "lng": 106.76})
            assert res.status_code in (200, 201, 422), f"{ky!r} trả {res.status_code}"
            assert "Traceback" not in res.text


def test_ky_tu_la_trong_analytics_khong_ghi_ban_rac() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = consent(c)
        for ky in KY_TU_LA:
            res = post_collect(c, receipt, [{"name": "page_viewed", "properties": {"query": ky}}])
            assert res.status_code == 200
        mongo = MongoClient(settings.mongodb_uri)
        db = mongo[settings.mongodb_db_name]
        so = db["analytics_events"].count_documents({})
        # Sự kiện vẫn được ghi, nhưng thuộc tính bị cắt/cam lọc, không phình vô hạn.
        mau = db["analytics_events"].find_one({"properties.query": {"$exists": True}})
        mongo.close()
        assert so == len(KY_TU_LA)
        assert len(mau["properties"]["query"]) <= 200


def test_no_sql_injection_khong_doi_cau_truy_van() -> None:
    """`$ne` trong input không được biến thành điều kiện truy vấn (SEC-008)."""
    nap_sach()
    with TestClient(app) as c:
        res = c.post("/analytics/consent", json={"anonymous_id": {"$ne": None}, "granted": True})
        assert res.status_code == 422
        # ID sai định dạng phải là 400 chứ không phải 500.
        assert c.get("/poi/%24ne").status_code == 400


# --- Trùng lặp ---


def test_ghi_trung_khong_sinh_ban_ghi_rac() -> None:
    nap_sach()
    with TestClient(app) as c:
        for _ in range(5):
            consent(c)
        mongo = MongoClient(settings.mongodb_uri)
        dem = mongo[settings.mongodb_db_name]["analytics_consents"].count_documents({"anonymous_id": ANON})
        mongo.close()
    assert dem == 1


def test_cung_mot_su_kien_ghi_nhieu_lan_thi_van_dem_dung() -> None:
    nap_sach()
    with TestClient(app) as c:
        receipt = consent(c)
        for _ in range(3):
            post_collect(c, receipt, [{"name": "page_viewed"}], heartbeat=False)
        mongo = MongoClient(settings.mongodb_uri)
        dem = mongo[settings.mongodb_db_name]["analytics_events"].count_documents({"name": "page_viewed"})
        phien = mongo[settings.mongodb_db_name]["analytics_sessions"].count_documents({"session_id": SESSION})
        mongo.close()
    assert dem == 3
    assert phien == 1


# --- Đồng thời ---


def test_ghi_dong_bo_chi_tao_mot_job() -> None:
    """Nhiều request cùng lúc không được tạo nhiều job tổng hợp cho một ngày."""
    from app.services import analytics_svc as an
    from app.services.analytics_read import chay_ngay

    nap_sach()
    ngay = "2026-03-25"

    async def chay() -> int:
        from motor.motor_asyncio import AsyncIOMotorClient

        db = AsyncIOMotorClient(settings.mongodb_uri)[settings.mongodb_db_name]
        await db["analytics_jobs"].drop()
        await db["analytics_events"].delete_many({})
        await an.dam_bao_index(db)
        await asyncio.gather(*(an.xep_viec_tong_hop(db, ngay) for _ in range(20)))
        dem = await db["analytics_jobs"].count_documents({"metric_date": ngay})
        await chay_ngay(db, ngay)
        return dem

    assert asyncio.run(chay()) == 1


def test_vuot_rate_limit_thi_vao_429_khong_phai_500() -> None:
    """Đẩy vượt ngưỡng phải ra 429 có Retry-After, không phải lỗi 500."""
    nap_sach()
    with TestClient(app) as c:
        receipt = consent(c)
        trang_thai = set()
        for _ in range(80):
            trang_thai.add(post_collect(c, receipt, [], heartbeat=False).status_code)
        assert trang_thai <= {200, 429}
        qua = post_collect(c, receipt, [], heartbeat=False)
        if qua.status_code == 429:
            assert "Retry-After" in qua.headers


def test_request_dong_bo_khong_lam_hong_server() -> None:
    """Nhiều thread gọi cùng lúc: không được có 5xx.

    Dùng chung MỘT TestClient cho mọi thread. Không mở client riêng cho từng
    thread vì `app/db.py` giữ một client Motor toàn tiến trình (có chủ đích, để
    dùng chung connection pool); mỗi vòng lifespan sẽ gọi `close_db()` và xoá
    client đó, khiến các thread còn lại gặp RuntimeError. Ứng dụng thật chạy
    một lifespan cho cả tiến trình, nên test phải giống vậy.
    """
    nap_sach()
    nap_admin()
    ket_qua: list[int] = []
    khoa = threading.Lock()

    with TestClient(app) as c:
        def bam() -> None:
            res = c.get("/poi/nearby?lat=10.7569&lng=106.7641&radius_m=1500")
            with khoa:
                ket_qua.append(res.status_code)

        tien_trinh = [threading.Thread(target=bam) for _ in range(6)]
        for t in tien_trinh:
            t.start()
        for t in tien_trinh:
            t.join(timeout=60)

    assert len(ket_qua) == 6
    assert all(m < 500 for m in ket_qua), f"có 5xx: {ket_qua}"