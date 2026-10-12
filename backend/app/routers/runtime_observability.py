"""Kênh quan sát vị trí runtime — TÁCH RIÊNG khỏi analytics (ANA-005).

Route công khai, không đòi consent: mục đích là chẩn đoán vận hành (GPS có
chạy không, độ chính xác bao nhiêu) chứ không phải đo hành vi khách. Đây là
lý do file này không import `analytics_svc` — trộn hai làn là mất ý nghĩa.

Bốn ràng buộc được kiểm soát ở đây, không tin client: origin, rate limit riêng
(60/phút IP, 20/phút phiên), kích thước ≤16 KiB, và mọi trường môi trường
client gửi kèm bị loại bỏ trước khi ghi.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.db import get_database
from app.services import runtime_observability as ro
from app.services.presence import origin_duoc_phep

router = APIRouter(prefix="/runtime-observability", tags=["runtime-observability"])

# Ngưỡng size đọc thẳng từ request để đo đúng byte thô client gửi.
NGAN_SACH = 32 * 1024


class LocationYeuCau(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    # Any chứ không phải dict: client thật hay gửi lô lẫn mẫu hỏng, muốn
    # từ chối từng mẫu và báo số rejected chứ không cả 422 cho cả lô.
    samples: list[Any] = Field(default_factory=list, max_length=ro.SO_MAU_TOI_DA)


@router.post("/location", summary="Gửi mẫu vị trí, không phụ thuộc consent analytics")
async def gui_vi_tri(body: LocationYeuCau, request: Request) -> dict:
    if not await origin_duoc_phep(request.headers.get("origin")):
        raise HTTPException(status_code=403, detail="Origin không được phép")
    # Đo payload thô trước khi parse để chặn vụ dồn dữ liệu.
    kich_thuoc = len(await request.body())
    if kich_thuoc > NGAN_SACH:
        raise HTTPException(status_code=413, detail="Payload quá lớn")
    if kich_thuoc > ro.KICH_THUOC_TOI_DA:
        raise HTTPException(status_code=413, detail="Payload vượt 16 KiB")

    db = get_database()
    await ro.dam_bao_index(db)
    ip = request.client.host if request.client else "la"
    ok, cho = await ro.kiem_tra_tan_suat(db, ip, body.session_id)
    if not ok:
        raise HTTPException(
            status_code=429, detail="Quá nhiều mẫu vị trí", headers={"Retry-After": str(cho)}
        )

    mau = [ro.lam_sach_mau(m) for m in body.samples[: ro.SO_MAU_TOI_DA]]
    ghi = await ro.ghi_vi_tri(db, mau)
    return {"accepted": ghi, "rejected": len(body.samples) - ghi}