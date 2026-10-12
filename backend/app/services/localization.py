"""Bản dịch POI ở collection riêng, khóa unique (poi_id, lang) (ADR-004)."""

from bson import ObjectId
from deep_translator import GoogleTranslator
from fastapi import HTTPException

NGON_NGU_UU_TIEN = ("vi", "en", "zh", "ja", "ko")


async def dam_bao_index(db) -> None:
    """Index unique để chèn trùng (poi_id, lang) bị từ chối."""
    await db["poi_localizations"].create_index([("poi_id", 1), ("lang", 1)], unique=True)


def dich_van_ban(van_ban: str, dich: str) -> str:
    """Bọc deep-translator, lỗi mạng trả 502 gọn chứ không treo."""
    try:
        return GoogleTranslator(source="auto", target=dich).translate(van_ban)
    except Exception:
        raise HTTPException(status_code=502, detail="Dịch vụ dịch tạm lỗi") from None


async def dich_va_luu(db, poi_id: ObjectId, lang: str) -> dict:
    """Dịch tên+mô tả POI rồi upsert vào poi_localizations."""
    poi = await db["pois"].find_one({"_id": poi_id})
    if poi is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    ban_dich = {
        "poi_id": poi_id,
        "lang": lang,
        "name": dich_van_ban(poi["name"], lang),
        "description": dich_van_ban(poi.get("description", ""), lang),
        "audio_url": None,
    }
    await db["poi_localizations"].update_one(
        {"poi_id": poi_id, "lang": lang}, {"$set": ban_dich}, upsert=True
    )
    return ban_dich


async def lay_ban_dich(db, poi_id: ObjectId, lang: str) -> tuple[dict | None, bool]:
    """Fallback 3 tầng: yêu cầu → en → vi, trả kèm cờ is_fallback."""
    truc_tiep = await db["poi_localizations"].find_one({"poi_id": poi_id, "lang": lang})
    if truc_tiep:
        return truc_tiep, False
    if lang != "vi":
        tieng_anh = await db["poi_localizations"].find_one({"poi_id": poi_id, "lang": "en"})
        if tieng_anh:
            return tieng_anh, True
    tieng_viet = await db["poi_localizations"].find_one({"poi_id": poi_id, "lang": "vi"})
    if tieng_viet:
        return tieng_viet, lang != "vi"
    return None, True


def ghep_poi(doc: dict, ban_dich: dict | None, is_fallback: bool, lang: str) -> dict:
    """Ghép POI gốc với bản dịch, rơi về vi thì audio_url null."""
    if ban_dich is None:
        return {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "description": doc.get("description", ""),
            "lat": doc["lat"],
            "lng": doc["lng"],
            "trigger_radius": doc.get("trigger_radius", 30),
            "audio_priority": doc.get("audio_priority", 0),
            "lang": lang,
            "is_fallback": True,
            "audio_url": None,
        }
    return {
        "id": str(doc["_id"]),
        "name": ban_dich["name"],
        "description": ban_dich["description"],
        "lat": doc["lat"],
        "lng": doc["lng"],
        "trigger_radius": doc.get("trigger_radius", 30),
        "audio_priority": doc.get("audio_priority", 0),
        "lang": ban_dich["lang"],
        "is_fallback": is_fallback,
        "audio_url": None if (is_fallback and ban_dich["lang"] == "vi") else ban_dich.get("audio_url"),
    }
