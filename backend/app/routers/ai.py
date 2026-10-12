"""AI mô tả: owner 10 lượt/ngày, admin không giới hạn, timeout 30s."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth import YeuCauDangNhap
from app.db import get_database
from app.services.ai_svc import lay_provider

router = APIRouter(prefix="/ai", tags=["ai"])

GIOI_HAN_OWNER_NGAY = 10


class LamDepYeuCau(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


async def con_luot(username: str) -> bool:
    """Đếm lượt hôm nay của owner bằng Mongo, lượt 11 bị từ chối."""
    hom_nay = datetime.now(UTC).strftime("%Y-%m-%d")
    dem = await get_database()["ai_usage_limits"].count_documents(
        {"username": username, "ngay": hom_nay}
    )
    return dem < GIOI_HAN_OWNER_NGAY


@router.post("/enhance-description", summary="AI viết lại mô tả quán")
async def lam_dep_mo_ta(body: LamDepYeuCau, user: dict = YeuCauDangNhap) -> dict:
    db = get_database()
    if user.get("role") == "poi_owner":
        doc = await db["admin_users"].find_one({"username": user["username"]})
        if not doc or not doc.get("is_poi_owner_verified"):
            raise HTTPException(status_code=403, detail="Tài khoản chủ quán chưa được duyệt")
        if not await con_luot(user["username"]):
            raise HTTPException(status_code=429, detail="Hết 10 lượt AI hôm nay")
        await db["ai_usage_limits"].insert_one(
            {"username": user["username"], "ngay": datetime.now(UTC).strftime("%Y-%m-%d")}
        )
    try:
        ket_qua = await lay_provider().viet_lai(body.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    return {"text": ket_qua}
