"""Di chuyển dữ liệu POI cũ thành bản `vi`, giữ trường cũ để quay lui."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongodb_db_name]
    await db["poi_localizations"].create_index([("poi_id", 1), ("lang", 1)], unique=True)
    dem = 0
    async for poi in db["pois"].find():
        await db["poi_localizations"].update_one(
            {"poi_id": poi["_id"], "lang": "vi"},
            {
                "$set": {
                    "poi_id": poi["_id"],
                    "lang": "vi",
                    "name": poi["name"],
                    "description": poi.get("description", ""),
                    "audio_url": None,
                }
            },
            upsert=True,
        )
        dem += 1
    print(f"Di chuyển xong: {dem} bản vi, giữ nguyên trường cũ ở POI.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
