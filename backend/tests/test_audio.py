"""Test audio: HIT/MISS, task nền, phục hồi, ẩn POI chờ tiếng Anh."""

import asyncio
from datetime import UTC, datetime, timedelta

from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import settings

settings.mongodb_db_name = "amds_test"

from app.main import app  # noqa: E402


def nap_admin() -> None:
    mongo = MongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_db_name]
    db["pois"].delete_many({})
    db["poi_localizations"].delete_many({})
    db["audio_tasks"].delete_many({})
    db["admin_users"].delete_many({})
    from app.auth import bam_mat_khau

    db["admin_users"].insert_one(
        {"username": "admin", "password_hash": bam_mat_khau("admin123"), "role": "super_admin"}
    )
    mongo.close()


def dang_nhap(c: TestClient) -> None:
    assert c.post("/admin/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 200


def test_tts_hit_miss() -> None:
    nap_admin()
    with TestClient(app) as c:
        dang_nhap(c)
        r1 = c.post("/audio/tts", json={"text": "Xin chào", "lang": "vi"})
        assert r1.status_code == 200
        assert r1.headers["X-Cache"] == "MISS"
        r2 = c.post("/audio/tts", json={"text": "Xin chào", "lang": "vi"})
        assert r2.headers["X-Cache"] == "HIT"


def test_task_pause_cancel() -> None:
    nap_admin()
    with TestClient(app) as c:
        dang_nhap(c)
        res = c.post("/audio/tasks/ma-gia/pause")
        assert res.status_code == 404
        res = c.post("/audio/tasks/ma-gia/menh-lenh-la", )
        assert res.status_code == 400


def test_an_poi_cho_tieng_anh() -> None:
    from app.services.audio_svc import hoan_tat_audio, kich_hoat_sinh_audio

    async def kich_ban() -> tuple:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        pid = (await db["pois"].insert_one({"name": "Q", "lat": 1, "lng": 1})).inserted_id
        await db["poi_localizations"].insert_one(
            {"poi_id": pid, "lang": "vi", "name": "Q", "description": "N", "audio_url": None}
        )
        await kich_hoat_sinh_audio(db, pid, ("vi",))
        doc = await db["pois"].find_one({"_id": pid})
        assert doc["is_active"] is False
        await hoan_tat_audio(db, pid, "vi", "/a.mp3")
        assert (await db["pois"].find_one({"_id": pid}))["is_active"] is False
        await db["poi_localizations"].insert_one(
            {"poi_id": pid, "lang": "en", "name": "Q", "description": "N", "audio_url": None}
        )
        await hoan_tat_audio(db, pid, "en", "/e.mp3")
        assert (await db["pois"].find_one({"_id": pid}))["is_active"] is True
        client.close()
        return True

    assert asyncio.run(kich_ban()) is True


def test_khoi_phuc_tasks_treo() -> None:
    async def chay() -> int:
        from motor.motor_asyncio import AsyncIOMotorClient

        from app.services.tasks import QuanLyTasks

        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        await db["audio_tasks"].delete_many({})
        cu = datetime.now(UTC) - timedelta(minutes=10)
        await db["audio_tasks"].insert_one(
            {
                "task_id": "treo",
                "poi_id": str(ObjectId()),
                "lang": "vi",
                "status": "running",
                "progress": 10,
                "updated_at": cu,
            }
        )
        ql = QuanLyTasks()
        ql.gan_db(db)
        dem = await ql.khoi_phuc()
        doc = await db["audio_tasks"].find_one({"task_id": "treo"})
        client.close()
        assert doc["status"] == "queued"
        return dem

    assert asyncio.run(chay()) == 1
