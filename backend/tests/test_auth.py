"""Test đăng nhập, phiên cookie và CRUD admin."""

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.auth import bam_mat_khau
from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap_admin() -> None:
    """Xóa sạch rồi nạp 1 super admin mật khẩu admin123."""
    mongo = MongoClient(settings.mongodb_uri)
    col = mongo[settings.mongodb_db_name]["admin_users"]
    col.delete_many({})
    col.insert_one(
        {"username": "admin", "password_hash": bam_mat_khau("admin123"), "role": "super_admin"}
    )
    mongo[settings.mongodb_db_name]["pois"].delete_many({})
    mongo.close()


def dang_nhap(c: TestClient) -> None:
    res = c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200


def test_dang_nhap_dung() -> None:
    nap_admin()
    with TestClient(app) as c:
        res = c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200
        assert "access_token=" in res.headers.get("set-cookie", "")
        assert "HttpOnly" in res.headers.get("set-cookie", "")
        me = c.get("/admin/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "admin"


def test_sai_mat_khau_va_sai_ten_giong_nhau() -> None:
    nap_admin()
    with TestClient(app) as c:
        sai_pass = c.post("/admin/auth/login", json={"username": "admin", "password": "sai"})
        sai_ten = c.post("/admin/auth/login", json={"username": "khong-co", "password": "sai"})
        assert sai_pass.status_code == 401
        assert sai_ten.status_code == 401
        assert sai_pass.json()["detail"] == sai_ten.json()["detail"]


def test_thieu_token_401() -> None:
    with TestClient(app) as c:
        assert c.get("/admin/auth/me").status_code == 401
        assert c.delete("/admin/pois/000000000000000000000000").status_code == 401


def test_token_rac_401() -> None:
    with TestClient(app) as c:
        res = c.get("/admin/auth/me", headers={"Authorization": "Bearer rac"})
        assert res.status_code == 401


def test_refresh_va_logout() -> None:
    nap_admin()
    with TestClient(app) as c:
        dang_nhap(c)
        assert c.post("/admin/auth/refresh").status_code == 200
        assert c.post("/admin/auth/logout").status_code == 200
        c.cookies.clear()
        assert c.get("/admin/auth/me").status_code == 401


def test_crud_poi_admin() -> None:
    nap_admin()
    with TestClient(app) as c:
        assert c.post("/admin/pois", json={"name": "X", "lat": 1, "lng": 1}).status_code == 401
        dang_nhap(c)
        tao = c.post(
            "/admin/pois",
            json={"name": "Quán mới", "description": "Ngon", "lat": 10.75, "lng": 106.76},
        )
        assert tao.status_code == 201
        pid = tao.json()["id"]
        # POI mới tạm ẩn chờ audio tiếng Anh (POI-011).
        assert c.get(f"/poi/{pid}").status_code == 404
        sua = c.put(f"/admin/pois/{pid}", json={"name": "Quán sửa", "lat": 10.75, "lng": 106.76})
        assert sua.status_code == 200
        assert sua.json()["name"] == "Quán sửa"
        assert (
            c.put(
                "/admin/pois/000000000000000000000000", json={"name": "X", "lat": 1, "lng": 1}
            ).status_code
            == 404
        )
        assert c.delete(f"/admin/pois/{pid}").status_code == 204
        assert c.get(f"/poi/{pid}").status_code == 404


def test_validate_bien() -> None:
    nap_admin()
    with TestClient(app) as c:
        dang_nhap(c)
        assert c.post("/admin/pois", json={"name": "X", "lat": 91, "lng": 1}).status_code == 422
        assert (
            c.post(
                "/admin/pois", json={"name": "X", "lat": 1, "lng": 1, "trigger_radius": 500}
            ).status_code
            == 422
        )
        assert c.post("/admin/pois", json={"name": "", "lat": 1, "lng": 1}).status_code == 422
