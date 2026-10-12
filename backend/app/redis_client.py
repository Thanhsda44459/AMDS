"""Redis dùng chung: hiện diện và giới hạn tần suất, tắt thì fail-open."""

import asyncio

import redis.asyncio as aredis

from app.config import settings

_client: aredis.Redis | None = None
_loop: asyncio.AbstractEventLoop | None = None
_da_canh_bao = False


async def lay_redis() -> aredis.Redis | None:
    """Trả client hoặc None khi Redis tắt, app vẫn chạy (fail-open).

    Client gắn với event loop đã tạo nó. Đổi loop (script chạy `asyncio.run`,
    test tạo loop mới) thì client cũ treo nên phải dựng lại — nếu không,
    lệnh Redis sẽ ném lỗi "NoneType has no attribute send".
    """
    global _client, _loop, _da_canh_bao
    loop = asyncio.get_running_loop()
    if _client is not None and _loop is loop:
        return _client
    try:
        _client = aredis.from_url(settings.redis_url, socket_connect_timeout=2)
        _loop = loop
        await _client.ping()
        return _client
    except Exception:
        _client = None
        _loop = None
        if not _da_canh_bao:
            _da_canh_bao = True
            print("[redis] Redis tắt, hiện diện và limit Redis tạm nghỉ (fail-open).")
        return None


def dat_lai() -> None:
    """Cho test giả lập Redis tắt."""
    global _client, _loop
    _client = None
    _loop = None
