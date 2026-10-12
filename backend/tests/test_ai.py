"""Test AI: quota owner 10/ngày, admin không giới hạn, timeout có kiểm soát."""

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    db["admin_users"].delete_many({})
    db["ai_usage_limits"].delete_many({})
    from app.auth import bam_mat_khau

    db["admin_users"].insert_many(
        [
            {"username": "root", "password_hash": bam_mat_khau("pw123456"), "role": "super_admin"},
            {
                "username": "chu",
                "password_hash": bam_mat_khau("pw123456"),
                "role": "poi_owner",
                "is_poi_owner_verified": True,
            },
        ]
    )
    mongo.close()


def test_owner_10_luot_roi_429() -> None:
    nap()
    with TestClient(app) as c:
        assert c.post("/admin/auth/login", json={"username": "chu", "password": "pw123456"}).status_code == 200
        for _ in range(10):
            res = c.post("/ai/enhance-description", json={"text": "Phở ngon"})
            assert res.status_code == 200
            assert "text" in res.json()
        assert c.post("/ai/enhance-description", json={"text": "Phở ngon"}).status_code == 429


def test_admin_khong_gioi_han() -> None:
    nap()
    with TestClient(app) as c:
        assert c.post("/admin/auth/login", json={"username": "root", "password": "pw123456"}).status_code == 200
        for _ in range(12):
            assert c.post("/ai/enhance-description", json={"text": "Phở ngon"}).status_code == 200


def test_timeout_co_kiem_soat(monkeypatch) -> None:
    import httpx


    nap()
    settings.ai_provider = "http"
    settings.ai_api_url = "http://localhost:9"

    async def treo(*args, **kwargs):
        raise httpx.ConnectError("khoi dong")

    monkeypatch.setattr(httpx.AsyncClient, "post", treo)
    try:
        with TestClient(app) as c:
            assert c.post("/admin/auth/login", json={"username": "root", "password": "pw123456"}).status_code == 200
            res = c.post("/ai/enhance-description", json={"text": "Phở ngon"})
            assert res.status_code == 502
    finally:
        settings.ai_provider = "mock"
