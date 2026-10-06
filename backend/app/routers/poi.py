"""Router POI v1, route gọi DB trực tiếp, chưa có service layer."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from app.db import get_database

router = APIRouter(prefix="/poi", tags=["poi"])


def doi_poi(doc: dict) -> dict:
    """Đổi `_id` ObjectId thành chuỗi `id` để JSON hóa được."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "description": doc.get("description", ""),
        "lat": doc["lat"],
        "lng": doc["lng"],
    }


@router.get("", summary="Lấy danh sách POI")
async def lay_danh_sach() -> list[dict]:
    db = get_database()
    docs = await db["pois"].find().to_list(length=100)
    return [doi_poi(d) for d in docs]


@router.get("/{poi_id}", summary="Lấy một POI theo id")
async def lay_mot(poi_id: str) -> dict:
    try:
        oid = ObjectId(poi_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None
    db = get_database()
    doc = await db["pois"].find_one({"_id": oid})
    if doc is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return doi_poi(doc)
