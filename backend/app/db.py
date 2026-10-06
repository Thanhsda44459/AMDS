"""Kết nối MongoDB qua Motor (async client).

Module này cung cấp kết nối tới MongoDB dùng Motor — driver bất đồng bộ
chạy trên asyncio event loop (vòng lặp sự kiện xử lý tác vụ bất đồng bộ)
của FastAPI. Client được giữ dưới dạng singleton (một instance duy nhất
dùng chung toàn ứng dụng) để tái sử dụng connection pool và tránh mở lại
kết nối cho từng request.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

# Client dùng chung toàn app. `None` nghĩa là chưa gọi connect_db().
_client: AsyncIOMotorClient | None = None


def get_db_client() -> AsyncIOMotorClient:
    """Trả về Motor client. Raise nếu chưa connect_db() — fail-fast."""
    if _client is None:
        raise RuntimeError("MongoDB client chưa khởi tạo — connect_db() chưa gọi")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Trả về database handle, tên DB lấy từ config tập trung."""
    return get_db_client()[settings.mongodb_db_name]


async def connect_db() -> None:
    """Khởi tạo client từ config và ping thử để fail-fast lúc startup."""
    global _client
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        # serverSelectionTimeoutMS: giới hạn thời gian chờ chọn server,
        # giúp fail nhanh khi MongoDB chưa sẵn sàng thay vì treo mãi.
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
