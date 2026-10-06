"""Seed 3 POI mẫu ở Quận 4, chạy lại không nhân đôi.

Dùng update_one với upsert theo `name` để đạt tính idempotent
(gọi nhiều lần cho kết quả như gọi một lần).
"""

import asyncio
import sys
from pathlib import Path

# Cho phép chạy `python scripts/seed_poi.py` từ thư mục backend.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# 3 quán thật ở Quận 4, tọa độ lấy xấp xỉ trung tâm khu ăn uống.
POIS_MAU = [
    {
        "name": "Bánh mì chảo Quận 4",
        "description": "Bánh mì chảo pate trứng ốp la ăn kèm dưa chua.",
        "lat": 10.7569,
        "lng": 106.7641,
    },
    {
        "name": "Ốc Đào Quận 4",
        "description": "Quán ốc đêm đông khách ở Vĩnh Khánh.",
        "lat": 10.7582,
        "lng": 106.7663,
    },
    {
        "name": "Bún mắm Quận 4",
        "description": "Bún mắm miền Tây thơm mắm cá linh.",
        "lat": 10.7545,
        "lng": 106.7628,
    },
]


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongodb_db_name]
    for poi in POIS_MAU:
        await db["pois"].update_one(
            {"name": poi["name"]},
            {"$set": poi},
            upsert=True,
        )
    dem = await db["pois"].count_documents({})
    print(f"Seed xong: {dem} POI trong DB '{settings.mongodb_db_name}'.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
