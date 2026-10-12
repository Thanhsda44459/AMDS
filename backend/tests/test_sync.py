"""Test sync: ETag 304, load-all, delta cập nhật và xóa."""

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    for ten in ("pois", "poi_localizations", "meta", "deleted_pois", "admin_users"):
        db[ten].delete_many({})
    from app.auth import bam_mat_khau

    db["admin_users"].insert_one(
        {"username": "admin", "password_hash": bam_mat_khau("admin123"), "role": "super_admin"}
    )
    mongo.close()


def dang_nhap(c: TestClient) -> None:
    assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_load_all_304() -> None:
    nap()
    with TestClient(app) as c:
        r1 = c.get("/poi/load-all?lang=vi")
        assert r1.status_code == 200
        etag = r1.headers.get("ETag")
        assert etag
        assert r1.json()["sync_cursor"] == r1.json()["version"]
        r2 = c.get("/poi/load-all?lang=vi", headers={"If-None-Match": etag})
        assert r2.status_code == 304


def test_304_khong_duoc_co_body() -> None:
    """Hồi quy: 304 trả body rỗng, không phải chuỗi "null".

    `JSONResponse(content=None)` serialize ra "null" (4 byte) trong khi uvicorn
    chờ 0 byte theo chuẩn HTTP, nên server ném
    `RuntimeError: Response content longer than Content-Length` và trả 500.
    TestClient không đi qua lớp đó nên phải kiểm body trực tiếp, và ETag phải
    được giữ lại để client so sánh được ở lần sau.
    """
    nap()
    with TestClient(app) as c:
        r1 = c.get("/poi/load-all?lang=vi")
        etag = r1.headers["ETag"]
        r2 = c.get("/poi/load-all?lang=vi", headers={"If-None-Match": etag})

    assert r2.status_code == 304
    assert r2.content == b""
    assert r2.headers.get("ETag") == etag
    assert r2.headers.get("content-length") in (None, "0")


def test_delta_cap_nhat_va_xoa() -> None:
    nap()
    with TestClient(app) as c:
        dang_nhap(c)
        tao = c.post("/admin/pois", json={"name": "Q", "lat": 1, "lng": 1})
        assert tao.status_code == 201
        v0 = c.get("/poi/delta?updated_after=0").json()["version"]
        d1 = c.get("/poi/delta?updated_after=0").json()
        assert v0 >= 1
        # POI mới đang processing nên ẩn khỏi delta công khai.
        assert d1["removed_poi_ids"] == []
        pid = tao.json()["id"]
        assert c.delete(f"/admin/pois/{pid}").status_code == 204
        d2 = c.get("/poi/delta?updated_after=0").json()
        assert pid in d2["removed_poi_ids"]
        assert d2["version"] > v0
        # Không đổi thì delta rỗng nhưng version giữ nguyên.
        d3 = c.get(f"/poi/delta?updated_after={d2['version']}").json()
        assert d3["updated"] == [] and d3["removed_poi_ids"] == []
