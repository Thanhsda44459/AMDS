"""Seed super admin đầu tiên từ biến môi trường, chạy lại không tạo trùng."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from app.auth import bam_mat_khau
from app.config import settings


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongodb_db_name]
    await db["admin_users"].create_index("username", unique=True)
    ket_qua = await db["admin_users"].update_one(
        {"username": settings.admin_username},
        {
            "$setOnInsert": {
                "password_hash": bam_mat_khau(settings.admin_password),
                "role": "super_admin",
            }
        },
        upsert=True,
    )
    if ket_qua.upserted_id is not None:
        print(f"Đã tạo super admin '{settings.admin_username}'. Đổi mật khẩu ngay khi deploy.")
    else:
        print(f"Super admin '{settings.admin_username}' đã có, giữ nguyên mật khẩu cũ.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
