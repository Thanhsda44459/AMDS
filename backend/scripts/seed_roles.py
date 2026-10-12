"""Seed 4 role mặc định, chạy lại không nhân đôi."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.permissions import dam_bao_roles


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    await dam_bao_roles(client[settings.mongodb_db_name])
    print("Seed roles xong: super_admin, admin, poi_owner, user.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
