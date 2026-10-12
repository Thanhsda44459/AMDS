"""Tùy chọn bản đồ offline: manifest no-cache, tải tệp an toàn."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.db import get_database
from app.services.maps import (
    SCOPES,
    THU_MUC_MAPS,
    duong_an_toan,
    manifest_audio_pack,
    manifest_scope,
)

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("/offline-options", summary="Các gói bản đồ offline")
async def tuy_chon() -> dict:
    return {"scopes": list(SCOPES), "note": "Chép tệp .pmtiles vào static/maps/<scope>/ rồi tải"}


@router.get("/manifest", summary="Manifest SHA-256 của scope")
async def manifest(scope: str = "quan4") -> JSONResponse:
    if scope not in SCOPES:
        scope = "quan4"
    return JSONResponse(content=manifest_scope(scope), headers={"Cache-Control": "no-cache"})


@router.get("/pack/{scope}/{ten_tep:path}", summary="Tải tệp pack, chặn path traversal")
async def tai_pack(scope: str, ten_tep: str) -> FileResponse:
    if scope not in SCOPES:
        raise HTTPException(status_code=404, detail="Không có scope")
    tep = duong_an_toan(f"{scope}/{ten_tep}")
    if not tep.is_file() or tep.suffix not in (".pmtiles", ".json"):
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    return FileResponse(
        str(tep),
        headers={"Cache-Control": "public, max-age=31536000, immutable", "Accept-Ranges": "bytes"},
    )


@router.get("/audio-pack", summary="Manifest gói audio theo ngôn ngữ")
async def audio_pack(lang: str = "vi") -> dict:
    return await manifest_audio_pack(get_database(), lang)


@router.get("/thu-muc", summary="Kiểm tra thư mục maps")
async def kiem_thu_muc() -> dict:
    THU_MUC_MAPS.mkdir(parents=True, exist_ok=True)
    return {"dir": str(THU_MUC_MAPS), "scopes": list(SCOPES)}
