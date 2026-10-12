"""Vị trí: nearby $geoNear kèm fallback Haversine khi hỏng index."""

import math

from fastapi import APIRouter, HTTPException

from app.db import get_database
from app.services.localization import dam_bao_index, ghep_poi, lay_ban_dich

router = APIRouter(prefix="/poi", tags=["poi-geo"])


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    s = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))


async def dam_bao_geo(db) -> None:
    """Backfill GeoJSON + index 2dsphere cho nearby."""
    await db["pois"].update_many(
        {"location": {"$exists": False}},
        [{"$set": {"location": {"type": "Point", "coordinates": ["$lng", "$lat"]}}}],
    )
    try:
        await db["pois"].create_index([("location", "2dsphere")])
    except Exception:
        pass


async def gan_khoang_cach(db, lat: float, lng: float, gioi_han_m: float, lang: str) -> list[dict]:
    """Đường $geoNear chính, hỏng thì Haversine dự phòng cho kết quả như nhau."""
    await dam_bao_index(db)
    await dam_bao_geo(db)
    try:
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "distanceField": "khoang_cach",
                    "maxDistance": gioi_han_m,
                    "query": {"is_active": {"$ne": False}},
                }
            },
            {"sort": {"khoang_cach": 1}},
        ]
        docs = await db["pois"].aggregate(pipeline).to_list(length=100)
    except Exception:
        docs = []
        async for d in db["pois"].find({"is_active": {"$ne": False}}):
            kc = haversine(lat, lng, d["lat"], d["lng"])
            if kc <= gioi_han_m:
                d["khoang_cach"] = kc
                docs.append(d)
        docs.sort(key=lambda d: d["khoang_cach"])
    ket_qua = []
    for d in docs:
        ban_dich, rot = await lay_ban_dich(db, d["_id"], lang)
        muc = ghep_poi(d, ban_dich, rot, lang)
        muc["distance_m"] = round(float(d.get("khoang_cach", 0)), 1)
        ket_qua.append(muc)
    return ket_qua


@router.get("/nearby", summary="POI gần nhất quanh vị trí")
async def gan_day(lat: float, lng: float, radius_m: float = 1500, lang: str = "vi") -> list[dict]:
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise HTTPException(status_code=400, detail="Tọa độ không hợp lệ")
    if not (0 < radius_m <= 5000):
        raise HTTPException(status_code=400, detail="Bán kính 1-5000m")
    return await gan_khoang_cach(get_database(), lat, lng, radius_m, lang)


@router.get("/hotset", summary="10 POI gần nhất trong 1.5km để hâm nóng")
async def hotset(lat: float, lng: float, lang: str = "vi") -> list[dict]:
    gan = await gan_khoang_cach(get_database(), lat, lng, 1500, lang)
    return gan[:10]
