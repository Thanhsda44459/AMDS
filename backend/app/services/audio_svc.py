"""Sinh audio Edge-TTS, cache theo MD5(text:lang), lưu audio_url."""

import hashlib
import time
from pathlib import Path

import edge_tts

THU_MUC_AUDIO = Path(__file__).resolve().parents[2] / "static" / "audio"
NGON_NGU_AUDIO = ("vi", "en", "zh", "ja", "ko")

GIONG: dict[str, str] = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
}


def khoa_cache(van_ban: str, lang: str) -> str:
    """Tên tệp theo nội dung, quên lang là va chạm cache."""
    return hashlib.md5(f"{van_ban}:{lang}".encode()).hexdigest() + ".mp3"


async def tao_mp3(van_ban: str, lang: str) -> bytes:
    """Sinh MP3 bằng Edge-TTS, lỗi mạng trả lỗi có kiểm soát."""
    try:
        am_thanh = b""
        async for mieng in edge_tts.Communicate(van_ban, GIONG.get(lang, GIONG["vi"])).stream():
            if mieng["type"] == "audio":
                am_thanh += mieng["data"]
        if not am_thanh:
            raise RuntimeError("TTS không trả audio")
        return am_thanh
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"TTS lỗi: {exc}") from exc


async def tao_mp3_cached(van_ban: str, lang: str) -> tuple[Path, bool]:
    """Tồn tại thì dùng lại (HIT), không thì sinh (MISS)."""
    THU_MUC_AUDIO.mkdir(parents=True, exist_ok=True)
    tep = THU_MUC_AUDIO / khoa_cache(van_ban, lang)
    if tep.exists():
        return tep, True
    tep.write_bytes(await tao_mp3(van_ban, lang))
    return tep, False


def duong_audio_url(ten_tep: str, lang: str, ban: int | None = None) -> str:
    """audio_url phiên bản hóa để cache busting khi nội dung đổi."""
    return f"/static/audio/{ten_tep}?v={ban or int(time.time())}&l={lang}"


async def kich_hoat_sinh_audio(db, poi_id, langs: tuple[str, ...] = NGON_NGU_AUDIO) -> list[str]:
    """Mô tả đổi thì xóa audio cũ, tạm ẩn POI chờ tiếng Anh xong."""
    await db["poi_localizations"].update_many(
        {"poi_id": poi_id}, {"$set": {"audio_url": None}}
    )
    await db["pois"].update_one(
        {"_id": poi_id},
        {"$set": {"audio_status": "processing", "is_active": False, "activation_requested": True}},
    )
    from app.services.tasks import quan_ly_tasks

    quan_ly_tasks.gan_db(db)
    ids = []
    for lang in langs:
        ids.append(await quan_ly_tasks.xep_viec(str(poi_id), lang))
    return ids


async def hoan_tat_audio(db, poi_id, lang: str, audio_url: str) -> None:
    """Worker gọi khi xong một ngôn ngữ, đủ tiếng Anh thì bật lại POI."""
    await db["poi_localizations"].update_one(
        {"poi_id": poi_id, "lang": lang}, {"$set": {"audio_url": audio_url}}
    )
    ban_en = await db["poi_localizations"].find_one({"poi_id": poi_id, "lang": "en"})
    if ban_en and ban_en.get("audio_url"):
        await db["pois"].update_one(
            {"_id": poi_id},
            {"$set": {"audio_status": "ready", "is_active": True, "activation_requested": False}},
        )
