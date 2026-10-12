"""Router POI công khai: danh sách, chi tiết, hydrate theo ngôn ngữ."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app.db import get_database
from app.services.localization import dam_bao_index, ghep_poi, lay_ban_dich
from app.services.sync import etag_cho, lay_phien_ban

router = APIRouter(prefix="/poi", tags=["poi"])


def doi_poi(doc: dict) -> dict:
    """Đổi `_id` ObjectId thành chuỗi `id` để JSON hóa được."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "description": doc.get("description", ""),
        "lat": doc["lat"],
        "lng": doc["lng"],
        "trigger_radius": doc.get("trigger_radius", 30),
        "audio_priority": doc.get("audio_priority", 0),
    }


@router.get("", summary="Lấy danh sách POI")
async def lay_danh_sach(lang: str = "vi") -> list[dict]:
    db = get_database()
    await dam_bao_index(db)
    docs = await db["pois"].find({"is_active": {"$ne": False}}).to_list(length=100)
    ket_qua = []
    for d in docs:
        ban_dich, rot = await lay_ban_dich(db, d["_id"], lang)
        ket_qua.append(ghep_poi(d, ban_dich, rot, lang))
    return ket_qua


@router.get("/load-all", summary="Tải toàn bộ POI kèm phiên bản sync")
async def tai_tat_ca(request: Request, lang: str = "vi") -> JSONResponse:
    db = get_database()
    await dam_bao_index(db)
    version = await lay_phien_ban(db)
    etag = etag_cho(version, lang)
    if request.headers.get("If-None-Match") == etag:
        # 304 bắt buộc không có body. `JSONResponse(content=None)` vẫn
        # serialize ra chuỗi "null", còn uvicorn chờ 0 byte theo chuẩn HTTP và
        # ném "Response content longer than Content-Length" → 500. Đây là
        # đường dẫn có thật: service worker và client sync đều dùng ETag.
        return Response(status_code=304, headers={"ETag": etag})
    docs = await db["pois"].find({"is_active": {"$ne": False}}).to_list(length=5000)
    ket_qua = []
    for d in docs:
        ban_dich, rot = await lay_ban_dich(db, d["_id"], lang)
        ket_qua.append(ghep_poi(d, ban_dich, rot, lang))
    return JSONResponse(
        content={"version": version, "sync_cursor": version, "pois": ket_qua},
        headers={"ETag": etag},
    )


@router.get("/delta", summary="Chỉ tải phần đổi từ updated_after")
async def tai_delta(updated_after: int = 0, lang: str = "vi") -> dict:
    db = get_database()
    await dam_bao_index(db)
    version = await lay_phien_ban(db)
    docs = await db["pois"].find({"version": {"$gt": updated_after}}).to_list(length=5000)
    cap_nhat = []
    for d in docs:
        if d.get("is_active") is False:
            continue
        ban_dich, rot = await lay_ban_dich(db, d["_id"], lang)
        cap_nhat.append(ghep_poi(d, ban_dich, rot, lang))
    mo_xoa = await db["deleted_pois"].find({"version": {"$gt": updated_after}}).to_list(length=5000)
    return {
        "version": version,
        "sync_cursor": version,
        "updated": cap_nhat,
        "removed_poi_ids": [str(m["poi_id"]) for m in mo_xoa],
    }


@router.get("/{poi_id}", summary="Lấy một POI theo id")
async def lay_mot(poi_id: str, lang: str = "vi") -> dict:
    try:
        oid = ObjectId(poi_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None
    db = get_database()
    await dam_bao_index(db)
    doc = await db["pois"].find_one({"_id": oid})
    if doc is None or doc.get("is_active") is False:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    ban_dich, rot = await lay_ban_dich(db, oid, lang)
    return ghep_poi(doc, ban_dich, rot, lang)
