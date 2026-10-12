"""Test luồng owner, PII Fernet, che PII 180 ngày."""

import asyncio
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"
settings.pii_key = Fernet.generate_key().decode()

from app.main import app  # noqa: E402


def nap_sach() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    for ten in ("admin_users", "owner_registrations", "owner_submissions", "owner_notifications", "pois"):
        db[ten].delete_many({})
    from app.auth import bam_mat_khau
    from app.permissions import dam_bao_roles

    async def nap() -> None:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(settings.mongodb_uri)
        await dam_bao_roles(client[settings.mongodb_db_name])
        client.close()

    asyncio.run(nap())
    db["admin_users"].insert_one(
        {"username": "root", "password_hash": bam_mat_khau("pw123456"), "role": "super_admin"}
    )
    mongo.close()


def test_luong_gui_duyet_thong_bao() -> None:
    nap_sach()
    with TestClient(app) as c:
        dk = c.post("/owner/register", json={"username": "chuquan", "password": "pw123456", "cccd": "123456789"})
        assert dk.status_code == 200
        trung = c.post("/owner/register", json={"username": "chuquan", "password": "pw123456", "cccd": "987654321"})
        assert trung.status_code == 400
        assert c.post("/admin/auth/login", json={"username": "chuquan", "password": "pw123456"}).status_code == 200
        gui = c.post("/owner/submissions", json={"name": "Q", "lat": 1, "lng": 1})
        assert gui.status_code == 403
    with TestClient(app) as a:
        assert a.post("/admin/auth/login", json={"username": "root", "password": "pw123456"}).status_code == 200
        tc = a.post("/owner/registrations/chuquan/reject", json={"admin_note": ""})
        assert tc.status_code == 400
        assert a.post("/owner/registrations/chuquan/approve").status_code == 200
    with TestClient(app) as c2:
        assert c2.post("/admin/auth/login", json={"username": "chuquan", "password": "pw123456"}).status_code == 200
        gui = c2.post("/owner/submissions", json={"name": "Quan chu", "description": "Ngon", "lat": 10.75, "lng": 106.76})
        assert gui.status_code == 200
        sid = gui.json()["submission_id"]
    with TestClient(app) as a2:
        assert a2.post("/admin/auth/login", json={"username": "root", "password": "pw123456"}).status_code == 200
        duyet = a2.post(f"/owner/submissions/{sid}/approve")
        assert duyet.status_code == 200
    with TestClient(app) as c3:
        assert c3.post("/admin/auth/login", json={"username": "chuquan", "password": "pw123456"}).status_code == 200
        tb = c3.get("/owner/notifications")
        assert tb.status_code == 200
        assert len(tb.json()) == 1
        nid = tb.json()[0]["id"]
        assert c3.post(f"/owner/notifications/{nid}/read").status_code == 200


def test_pii_ma_hoa_va_sai_khoa() -> None:
    from app.pii import giai_ma_pii, ma_hoa_pii

    ma = ma_hoa_pii("123456789")
    assert ma is not None and ma.startswith("v1:")
    assert giai_ma_pii(ma) == "123456789"
    settings.pii_key = Fernet.generate_key().decode()
    assert giai_ma_pii(ma) is None


def test_che_pii_180_ngay() -> None:
    from app.routers.owner import che_pii_cu

    async def chay() -> int:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        await db["admin_users"].delete_many({})
        cu = datetime.now(UTC) - timedelta(days=200)
        await db["admin_users"].insert_one(
            {"username": "cu", "cccd_encrypted": "v1:gia", "pii_created_at": cu, "pii_masked": False}
        )
        dem = await che_pii_cu(db, datetime.now(UTC))
        doc = await db["admin_users"].find_one({"username": "cu"})
        client.close()
        assert doc["cccd_encrypted"] is None and doc["pii_masked"] is True
        return dem

    assert asyncio.run(chay()) == 1
