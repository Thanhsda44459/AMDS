"""Test P9: bundle pending/ready, nearby hai đường, rate limit 429."""

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    for ten in ("pois", "poi_localizations", "admin_users", "ui_bundles", "rate_limits"):
        db[ten].delete_many({})
    from app.auth import bam_mat_khau

    db["admin_users"].insert_one(
        {"username": "admin", "password_hash": bam_mat_khau("admin123"), "role": "super_admin"}
    )
    db["pois"].insert_one({"name": "Q", "description": "N", "lat": 10.7569, "lng": 106.7641})
    mongo.close()


def dang_nhap(c: TestClient) -> None:
    assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_bundle_chinh_ready() -> None:
    with TestClient(app) as c:
        for locale in ("vi", "en", "zh", "ja", "ko"):
            res = c.get(f"/ui-bundles/{locale}")
            assert res.status_code == 200
            assert res.json()["status"] == "ready"
            assert "app_title" in res.json()["bundle"]


def test_bundle_la_pending() -> None:
    nap()
    with TestClient(app) as c:
        r1 = c.get("/ui-bundles/xx")
        assert r1.status_code == 200
        assert r1.json()["status"] in ("pending", "ready")
        assert r1.json()["bundle"]["app_title"]


def test_nearby_va_hotset() -> None:
    nap()
    with TestClient(app) as c:
        gan = c.get("/poi/nearby?lat=10.7569&lng=106.7641&radius_m=1500")
        assert gan.status_code == 200
        assert len(gan.json()) == 1
        assert gan.json()[0]["distance_m"] < 5
        hot = c.get("/poi/hotset?lat=10.7569&lng=106.7641")
        assert hot.status_code == 200
        xa = c.get("/poi/nearby?lat=0&lng=0&radius_m=100")
        assert xa.json() == []
        sai = c.get("/poi/nearby?lat=200&lng=0")
        assert sai.status_code == 400


def test_ratelimit_429() -> None:
    from app.services.ratelimit import CUA_SO_PHUT, GIOI_HAN

    assert GIOI_HAN == 30 and CUA_SO_PHUT == 10
    nap()
    with TestClient(app) as c:
        dang_nhap(c)
        for _ in range(30):
            res = c.post("/audio/tts", json={"text": "x", "lang": "vi"})
            assert res.status_code in (200, 502)
        qua = c.post("/audio/tts", json={"text": "x", "lang": "vi"})
        assert qua.status_code == 429
        assert "Retry-After" in qua.headers
