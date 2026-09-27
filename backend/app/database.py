
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_db_client() -> AsyncIOMotorClient:
    """Trả về motor client. Raise nếu chưa connect_db() — fail-fast."""
    if _client is None:
        raise RuntimeError("MongoDB client chưa khởi tạo — connect_db() chưa gọi")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Trả về database handle theo MONGODB_DB_NAME."""
    db_name = os.getenv("MONGODB_DB_NAME", "AMSD")
    return get_db_client()[db_name]


async def connect_db() -> None:
    """Khởi tạo client + ping thử để fail-fast lúc startup."""
    global _client
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    _client = AsyncIOMotorClient(
        mongo_uri,
        serverSelectionTimeoutMS=2000,
        connectTimeoutMS=2000,
    )
    await _client.admin.command("ping")


async def close_db() -> None:
    """Đóng client khi shutdown — giải phóng connection pool."""
    global _client
    if _client is not None:
        _client.close()
        _client = None