"""API audio: TTS stream, on-demand dịch+TTS, tác vụ nền + SSE."""

import asyncio

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from app.auth import YeuCauDangNhap
from app.db import get_database
from app.services.audio_svc import (
    NGON_NGU_AUDIO,
    THU_MUC_AUDIO,
    duong_audio_url,
    hoan_tat_audio,
    tao_mp3_cached,
)
from app.services.localization import dam_bao_index, dich_va_luu
from app.services.ratelimit import khoa_cho, kiem_tra
from app.services.tasks import quan_ly_tasks

router = APIRouter(prefix="/audio", tags=["audio"])


class TtsYeuCau(BaseModel):
    text: str
    lang: str = "vi"


class OnDemandYeuCau(BaseModel):
    poi_id: str
    lang: str


@router.post("/tts", summary="Văn bản thành MP3 stream (Tier 2)")
async def tts(body: TtsYeuCau, request: Request, user: dict = YeuCauDangNhap) -> Response:
    await kiem_tra(get_database(), khoa_cho(request, user), "/audio/tts")
    try:
        tep, hit = await tao_mp3_cached(body.text, body.lang)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    return Response(
        content=tep.read_bytes(),
        media_type="audio/mpeg",
        headers={"X-Cache": "HIT" if hit else "MISS"},
    )


@router.post("/on-demand", summary="Dịch + TTS cho POI thiếu audio (Tier 1.5)")
async def on_demand(body: OnDemandYeuCau, request: Request, user: dict = YeuCauDangNhap) -> dict:
    try:
        oid = ObjectId(body.poi_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None
    db = get_database()
    await kiem_tra(db, khoa_cho(request, user), "/audio/on-demand")
    await dam_bao_index(db)
    ban_dich = await db["poi_localizations"].find_one({"poi_id": oid, "lang": body.lang})
    if not ban_dich:
        ban_dich = await dich_va_luu(db, oid, body.lang)
    try:
        tep, _hit = await tao_mp3_cached(ban_dich["description"] or ban_dich["name"], body.lang)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    url = duong_audio_url(tep.name, body.lang)
    await hoan_tat_audio(db, oid, body.lang, url)
    return {"poi_id": body.poi_id, "lang": body.lang, "audio_url": url}


@router.get("/tasks", summary="Liệt kê tác vụ audio")
async def liet_ke_tasks(_user: dict = YeuCauDangNhap) -> list[dict]:
    docs = await get_database()["audio_tasks"].find().sort("updated_at", -1).to_list(length=100)
    for d in docs:
        d.pop("_id", None)
        ts = d.get("updated_at")
        d["updated_at"] = ts.isoformat() if ts else None
    return docs


@router.get("/tasks/stream", summary="SSE tiến độ tác vụ")
async def stream_tasks(_user: dict = YeuCauDangNhap) -> StreamingResponse:
    hang_doi: asyncio.Queue = asyncio.Queue(maxsize=50)
    quan_ly_tasks.nguoi_nghe.add(hang_doi)

    async def sinh():
        try:
            yield ": mo ket noi\n\n"
            while True:
                try:
                    sk = await asyncio.wait_for(hang_doi.get(), timeout=5)
                    yield f"data: {sk['task_id']}:{sk['status']}\n\n"
                except TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            quan_ly_tasks.nguoi_nghe.discard(hang_doi)

    return StreamingResponse(sinh(), media_type="text/event-stream")


@router.post("/tasks/{task_id}/{lenh}", summary="Pause/resume/cancel tác vụ")
async def dieu_khien_task(task_id: str, lenh: str, _user: dict = YeuCauDangNhap) -> dict:
    if lenh not in ("pause", "resume", "cancel"):
        raise HTTPException(status_code=400, detail="Lệnh không hợp lệ")
    ok = await quan_ly_tasks.dieu_khien(task_id, lenh)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ")
    return {"ok": True}


@router.get("/giong", summary="Giọng TTS theo ngôn ngữ")
async def liet_ke_giong() -> dict:
    from app.services.audio_svc import GIONG

    return {"langs": list(NGON_NGU_AUDIO), "voices": GIONG, "cache_dir": str(THU_MUC_AUDIO)}
