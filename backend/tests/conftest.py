"""Mock dịch và TTS cho mọi test để offline, nhanh, logic thật."""

import pytest

from app.config import settings


@pytest.fixture(scope="session", autouse=True)
def kiem_tra_ha_tang() -> None:
    """Fail sớm và rõ khi Mongo chưa lên, thay vì 59 test đỏ vì lỗi kết nối.

    Không có bước này, `pytest` với Mongo tắt sẽ treo hàng chục phút rồi báo
    một loạt failure giống hệt nhau — rất dễ tưởng là test hỏng thật.
    """
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    try:
        MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000).admin.command("ping")
    except PyMongoError as exc:
        pytest.exit(
            f"Không kết nối được MongoDB tại {settings.mongodb_uri}.\n"
            "Chạy `docker compose up -d --wait` ở thư mục gốc rồi thử lại.\n"
            f"Chi tiết: {type(exc).__name__}",
            returncode=1,
        )


@pytest.fixture(autouse=True)
def xoa_luong_redis():
    """Dọn bộ đếm rate limit trong Redis trước mỗi test.

    Rate limit analytics đếm bằng Redis (`quan4:rl:*`), còn rate limit chung
    đếm bằng Mongo. Xoá `rate_limits` trong Mongo **không** xoá phần Redis, nên
    test sau sẽ dính 429 của test trước. Với Redis tắt thì bỏ qua, đó cũng là
    hành vi fail-open cần kiểm chứng.
    """
    import asyncio as _asyncio

    async def don() -> None:
        from app.redis_client import lay_redis

        redis = await lay_redis()
        if redis is None:
            return
        khoa = [k async for k in redis.scan_iter(match="quan4:rl:*")]
        if khoa:
            await redis.delete(*khoa)

    _asyncio.run(don())
    yield


@pytest.fixture(autouse=True)
def mang_gia(monkeypatch, tmp_path):
    import app.services.audio_svc as am
    import app.services.localization as loc

    monkeypatch.setattr(am, "THU_MUC_AUDIO", tmp_path)

    async def mp3_gia(van_ban: str, lang: str) -> bytes:
        return b"ID3" + van_ban.encode()[:10]

    monkeypatch.setattr(am, "tao_mp3", mp3_gia)
    monkeypatch.setattr(loc, "dich_van_ban", lambda van_ban, lang: f"{van_ban} [{lang}]")
