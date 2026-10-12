"""Test fallback 3 tầng, on-demand upsert, index unique."""

from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap_du_lieu() -> str:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    db["pois"].delete_many({})
    db["poi_localizations"].delete_many({})
    db["admin_users"].delete_many({})
    from app.auth import bam_mat_khau

    db["admin_users"].insert_one(
        {"username": "admin", "password_hash": bam_mat_khau("admin123"), "role": "super_admin"}
    )
    pid = db["pois"].insert_one(
        {"name": "Phở", "description": "Ngon", "lat": 10.75, "lng": 106.76}
    ).inserted_id
    db["poi_localizations"].insert_many(
        [
            {"poi_id": pid, "lang": "vi", "name": "Phở", "description": "Ngon", "audio_url": None},
            {"poi_id": pid, "lang": "en", "name": "Pho", "description": "Tasty", "audio_url": "/a.mp3"},
        ]
    )
    mongo.close()
    return str(pid)


def dang_nhap(c: TestClient) -> None:
    assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_roi_vi_ve_vi() -> None:
    pid = nap_du_lieu()
    with TestClient(app) as c:
        res = c.get(f"/poi/{pid}?lang=vi")
        assert res.status_code == 200
        assert res.json()["is_fallback"] is False


def test_co_ban_dich_en() -> None:
    pid = nap_du_lieu()
    with TestClient(app) as c:
        res = c.get(f"/poi/{pid}?lang=en")
        assert res.json()["name"] == "Pho"
        assert res.json()["is_fallback"] is False


def test_roi_ve_en_khi_thieu_ja() -> None:
    pid = nap_du_lieu()
    with TestClient(app) as c:
        res = c.get(f"/poi/{pid}?lang=ja")
        data = res.json()
        assert data["is_fallback"] is True
        assert data["lang"] == "en"


def test_on_demand_upsert() -> None:
    nap_du_lieu()
    with TestClient(app) as c:
        dang_nhap(c)
        r1 = c.post("/localizations/on-demand", json={"poi_id": "x", "lang": "ja"})
        assert r1.status_code == 400
        pid = c.get("/poi").json()[0]["id"]
        r2 = c.post("/localizations/on-demand", json={"poi_id": pid, "lang": "ja"})
        assert r2.status_code == 200
        r3 = c.post("/localizations/on-demand", json={"poi_id": pid, "lang": "ja"})
        assert r3.status_code == 200
        mongo = MongoClient(settings.mongodb_uri)
        dem = mongo[settings.mongodb_db_name]["poi_localizations"].count_documents(
            {"poi_id": ObjectId(pid), "lang": "ja"}
        )
        mongo.close()
        assert dem == 1


def test_trung_khoa_bi_tu_choi() -> None:
    from pymongo.errors import DuplicateKeyError

    nap_du_lieu()
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    pid = db["pois"].find_one()["_id"]
    try:
        db["poi_localizations"].insert_one({"poi_id": pid, "lang": "vi", "name": "X"})
        raise AssertionError("trùng khóa phải bị từ chối")
    except DuplicateKeyError:
        pass
    finally:
        mongo.close()
