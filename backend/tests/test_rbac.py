"""Test ma trận role × route và audit log."""

from fastapi.testclient import TestClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402
from app.permissions import dam_bao_roles  # noqa: E402


def nap_roles_va_users() -> None:
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    from app.auth import bam_mat_khau

    async def nap() -> None:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        await dam_bao_roles(db)
        await db["admin_users"].delete_many({})
        for ten, role in (("root", "super_admin"), ("quanly", "admin"), ("chu", "poi_owner")):
            await db["admin_users"].insert_one(
                {"username": ten, "password_hash": bam_mat_khau("pw123456"), "role": role}
            )
        client.close()

    asyncio.run(nap())


def dang_nhap(c: TestClient, ten: str) -> None:
    assert c.post("/admin/auth/login", json={"username": ten, "password": "pw123456"}).status_code == 200


def test_owner_xoa_bi_403() -> None:
    nap_roles_va_users()
    with TestClient(app) as c:
        dang_nhap(c, "chu")
        res = c.delete("/admin/pois/000000000000000000000000")
        assert res.status_code == 403


def test_admin_xem_roles_bi_403_super_duoc() -> None:
    nap_roles_va_users()
    with TestClient(app) as c:
        dang_nhap(c, "quanly")
        assert c.get("/admin/roles").status_code == 403
    with TestClient(app) as c2:
        dang_nhap(c2, "root")
        res = c2.get("/admin/roles")
        assert res.status_code == 200
        ten_roles = [r["name"] for r in res.json()]
        assert set(("super_admin", "admin", "poi_owner", "user")) <= set(ten_roles)


def test_admin_xem_audit() -> None:
    nap_roles_va_users()
    with TestClient(app) as c:
        dang_nhap(c, "quanly")
        tao = c.post("/admin/pois", json={"name": "Q", "lat": 1, "lng": 1})
        assert tao.status_code == 201
        logs = c.get("/admin/audit-logs")
        assert logs.status_code == 200
        assert any(dong["action"] == "poi:create" for dong in logs.json())


def test_khach_khong_vao_admin() -> None:
    with TestClient(app) as c:
        assert c.get("/admin/audit-logs").status_code == 401
        assert c.get("/admin/roles").status_code == 401
