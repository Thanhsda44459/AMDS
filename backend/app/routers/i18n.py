"""UI bundle hai làn: 5 ngôn ngữ tĩnh, còn lại dịch nền + source_hash."""

import asyncio
import hashlib
import json
from pathlib import Path

from fastapi import APIRouter

from app.db import get_database
from app.services.localization import dich_van_ban

router = APIRouter(prefix="/ui-bundles", tags=["i18n"])

THU_MUC_UI = Path(__file__).resolve().parents[2] / "static" / "ui"
NGON_NGU_CHINH = ("vi", "en", "zh", "ja", "ko")


def doc_bundle_tinh(locale: str) -> dict | None:
    tep = THU_MUC_UI / f"{locale}.json"
    if not tep.is_file():
        return None
    return json.loads(tep.read_text(encoding="utf-8"))


def source_hash(bundle_en: dict) -> str:
    return hashlib.md5(json.dumps(bundle_en, sort_keys=True).encode()).hexdigest()


@router.get("/{locale}", summary="Bundle UI, lạ thì tiếng Anh + pending")
async def lay_bundle(locale: str) -> dict:
    bundle_en = doc_bundle_tinh("en") or {}
    if locale in NGON_NGU_CHINH:
        bundle = doc_bundle_tinh(locale) or bundle_en
        return {"locale": locale, "status": "ready", "bundle": bundle, "source_hash": source_hash(bundle_en)}
    db = get_database()
    ban = await db["ui_bundles"].find_one({"locale": locale})
    hash_hien_tai = source_hash(bundle_en)
    if ban and ban.get("status") == "ready" and ban.get("source_hash") == hash_hien_tai:
        return {"locale": locale, "status": "ready", "bundle": ban["bundle"], "source_hash": hash_hien_tai}
    if not ban or ban.get("status") != "translating":
        await db["ui_bundles"].update_one(
            {"locale": locale},
            {"$set": {"locale": locale, "status": "translating", "source_hash": hash_hien_tai}},
            upsert=True,
        )
        asyncio.create_task(dich_nen(locale, bundle_en, hash_hien_tai))
    return {"locale": locale, "status": "pending", "bundle": bundle_en, "source_hash": hash_hien_tai}


async def dich_nen(locale: str, bundle_en: dict, hash_moi: str) -> None:
    """Dịch long-tail nền từng khóa, xong thì ready."""
    try:
        from app.db import get_database as _db

        db = _db()
        ket_qua = {}
        for khoa, gia_tri in bundle_en.items():
            try:
                ket_qua[khoa] = dich_van_ban(str(gia_tri), locale)
            except Exception:
                ket_qua[khoa] = gia_tri
        await db["ui_bundles"].update_one(
            {"locale": locale},
            {"$set": {"bundle": ket_qua, "status": "ready", "source_hash": hash_moi}},
        )
    except Exception:
        pass
