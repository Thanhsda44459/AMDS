"""Hâm nóng corpus: dịch nền toàn bộ bản thiếu, xem trạng thái."""

import asyncio

from fastapi import APIRouter

from app.auth import doi_quyen
from app.db import get_database
from app.services.localization import NGON_NGU_UU_TIEN, dam_bao_index, dich_va_luu

router = APIRouter(prefix="/localizations", tags=["localizations-warmup"])

DuocCapNhatPoi = doi_quyen("poi:update")

_trang_thai: dict = {"running": False, "done": 0, "total": 0}


@router.post("/warmup", summary="Dịch nền toàn corpus thiếu")
async def ham_nong(_user: dict = DuocCapNhatPoi) -> dict:
    if _trang_thai["running"]:
        return {"ok": True, "note": "đang chạy"}
    _trang_thai.update({"running": True, "done": 0, "total": 0})
    asyncio.create_task(_chay_nen())
    return {"ok": True}


async def _chay_nen() -> None:
    try:
        db = get_database()
        await dam_bao_index(db)
        pois = await db["pois"].find().to_list(length=5000)
        langs = [lang for lang in NGON_NGU_UU_TIEN if lang != "vi"]
        _trang_thai["total"] = len(pois) * len(langs)
        for poi in pois:
            for lang in langs:
                if not await db["poi_localizations"].find_one({"poi_id": poi["_id"], "lang": lang}):
                    try:
                        await dich_va_luu(db, poi["_id"], lang)
                    except Exception:
                        pass
                _trang_thai["done"] += 1
    finally:
        _trang_thai["running"] = False


@router.get("/warmup-status", summary="Tiến độ hâm nóng")
async def trang_thai_ham_nong(_user: dict = DuocCapNhatPoi) -> dict:
    return dict(_trang_thai)
