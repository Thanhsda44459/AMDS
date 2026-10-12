"""Hiện diện ẩn danh bằng Redis: cửa sổ trượt đếm THIẾT BỊ, không đếm tab.

Một thiết bị = một `anonymous_id`. Nhiều tab trên cùng thiết bị chỉ tính một
lần vì ZSET khóa theo chính `anonymous_id` — đó là lý do không được dùng
session_id làm phần tử ZSET. Kết quả là `tracked_online_users` là số thiết bị
đã đồng ý còn trong cửa sổ, không phải tổng lượt truy cập hay số tab mở.

Redis tắt thì **fail-open**: trả `None` để lớp trên hiển thị "không có số
liệu hiện diện" thay vì báo `0` sai lệch. Sự kiện analytics vẫn ghi bình
thường vì hiện diện chỉ là số liệu phụ (ADR-010).
"""

import time

from app.config import settings
from app.redis_client import lay_redis

KHOA_ZSET = "quan4:analytics:presence"

# Cửa sổ trượt 5 phút: đóng app quá 5 phút thì tự rơi khỏi số đang online.
CUA_SO_GIOY = 300
# TTL cho key gấp đôi cửa sổ để không mất dữ liệu giữa hai lần quét.
TTL_GIOY = CUA_SO_GIOY * 2


async def _cat_cua_so(redis, bay_sang: float) -> int:
    """Xóa mốc cũ ngoài cửa sổ rồi đếm phần tử còn lại."""
    await redis.zremrangebyscore(KHOA_ZSET, "-inf", bay_sang)
    await redis.expire(KHOA_ZSET, TTL_GIOY)
    return int(await redis.zcard(KHOA_ZSET))


async def heartbeat(anonymous_id: str) -> int | None:
    """Ghi nhận thiết bị đang hoạt động, trả số thiết bị đang online.

    Chỉ được gọi sau khi đã qua cổng consent — thiết bị chưa đồng ý thì
    không được vào cửa sổ hiện diện.
    """
    if not anonymous_id:
        return None
    redis = await lay_redis()
    if redis is None:
        return None
    bay = time.time()
    try:
        await redis.zadd(KHOA_ZSET, {anonymous_id: bay})
        return await _cat_cua_so(redis, bay - CUA_SO_GIOY)
    except Exception:
        return None


async def dem_online() -> int | None:
    """Số thiết bị đã consent còn trong cửa sổ trượt. `None` khi Redis tắt."""
    redis = await lay_redis()
    if redis is None:
        return None
    try:
        return await _cat_cua_so(redis, time.time() - CUA_SO_GIOY)
    except Exception:
        return None


async def xoa_het() -> None:
    """Dọn cửa sổ hiện diện, dùng cho test và khi cần số liệu sạch."""
    redis = await lay_redis()
    if redis is None:
        return
    try:
        await redis.delete(KHOA_ZSET)
    except Exception:
        return


async def xoa_thiet_bi(anonymous_id: str) -> None:
    """Rút một thiết bị khỏi cửa sổ hiện diện (dùng khi thu hồi consent).

    Chỉ xoá đúng thiết bị đó. Xoá cả cửa sổ sẽ làm số `tracked_online_users` tụt
    về 0 trong khi những máy khác vẫn đang dùng app — số liệu sai lệch.
    """
    if not anonymous_id:
        return
    redis = await lay_redis()
    if redis is None:
        return
    try:
        await redis.zrem(KHOA_ZSET, anonymous_id)
    except Exception:
        return


async def origin_duoc_phep(origin: str | None) -> bool:
    """Chỉ nhận payload từ origin đã khai báo, chặn việc gọi chéo domain."""
    if not origin:
        return True
    return origin in settings.analytics_allowed_origins