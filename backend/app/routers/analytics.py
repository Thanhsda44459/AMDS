"""API thu thập analytics: cổng consent, heartbeat, lô sự kiện.

Đây là route công khai (khách không đăng nhập) nên không có `doi_quyen`.
Thay vào đó nó tự bảo vệ bằng cổng consent: không có receipt hợp lệ + consent
còn `granted` thì **không ghi gì** và trả 403. Sự kiện từ bot bị bỏ qua có
chủ đích, trả 202 chứ không phải lỗi — bot không biết mình bị lọc.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.db import get_database
from app.services import analytics_svc as an
from app.services.presence import dem_online, heartbeat, origin_duoc_phep, xoa_thiet_bi

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ConsentYeuCau(BaseModel):
    anonymous_id: str = Field(min_length=16, max_length=64)
    granted: bool


class SuKien(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    at: int | None = None
    properties: dict = Field(default_factory=dict)


class CollectYeuCau(BaseModel):
    anonymous_id: str = Field(min_length=16, max_length=64)
    receipt: str = Field(min_length=8, max_length=512)
    session_id: str = Field(min_length=8, max_length=64)
    heartbeat: bool = True
    events: list[SuKien] = Field(default_factory=list, max_length=50)


@router.get("/consent", summary="Trạng thái consent của thiết bị ẩn danh")
async def xem_consent(anonymous_id: str) -> dict:
    if not an.hop_le(anonymous_id):
        raise HTTPException(status_code=400, detail="anonymous_id không hợp lệ")
    db = get_database()
    await an.dam_bao_index(db)
    return {"anonymous_id": anonymous_id, "status": await an.trang_thai_consent(db, anonymous_id)}


@router.post("/consent", summary="Ghi nhận hoặc thu hồi consent")
async def dat_consent(body: ConsentYeuCau, request: Request) -> dict:
    if not an.hop_le(body.anonymous_id):
        raise HTTPException(status_code=400, detail="anonymous_id không hợp lệ")
    if not await origin_duoc_phep(request.headers.get("origin")):
        raise HTTPException(status_code=403, detail="Origin không được phép")
    db = get_database()
    await an.dam_bao_index(db)
    await an.dat_consent(db, body.anonymous_id, body.granted)
    if not body.granted:
        # Chỉ rút chính thiết bị này khỏi cửa sổ hiện diện; máy khác vẫn đang
        # dùng app thì số online phải giữ nguyên.
        await xoa_thiet_bi(body.anonymous_id)
        return {"status": "revoked", "receipt": None}
    return {"status": "granted", "receipt": an.lam_receipt(body.anonymous_id)}


@router.post("/collect", summary="Heartbeat + lô sự kiện, chỉ nhận khi đã consent")
async def thu_thap(body: CollectYeuCau, request: Request) -> dict:
    db = get_database()
    await an.dam_bao_index(db)

    if not an.hop_le(body.anonymous_id):
        raise HTTPException(status_code=400, detail="anonymous_id không hợp lệ")
    # Bot/crawler bị lọc trước cả bước xác thực receipt cho khỏi tốn băm.
    ly_do = an.ly_do_loc(request.headers.get("user-agent", ""))
    if ly_do is not None:
        return {"accepted": 0, "filtered": ly_do, "tracked_online_users": None}
    if not await origin_duoc_phep(request.headers.get("origin")):
        raise HTTPException(status_code=403, detail="Origin không được phép")

    receipt = an.doc_receipt(body.receipt)
    if receipt is None or receipt["anonymous_id"] != body.anonymous_id:
        raise HTTPException(status_code=403, detail="Thiếu hoặc sai receipt consent")
    if not await an.co_consent(db, body.anonymous_id):
        raise HTTPException(status_code=403, detail="Chưa đồng ý thu thập analytics")

    ip = request.client.host if request.client else "la"
    ok, cho = await an.cho_phep_luong(db, body.anonymous_id, ip)
    if not ok:
        raise HTTPException(
            status_code=429, detail="Quá nhiều yêu cầu analytics", headers={"Retry-After": str(cho)}
        )

    await an.cap_nhat_device(db, body.anonymous_id, request.headers.get("user-agent", ""))
    await an.cap_nhat_session(
        db, body.anonymous_id, body.session_id, request.headers.get("user-agent", "")
    )

    # Nhịp heartbeat 20s nên chỉ ghi mốc mới; lô sự kiện thì chỉ đọc số hiện diện.
    if body.heartbeat:
        online = await heartbeat(body.anonymous_id)
    else:
        online = await dem_online()

    nhan = 0
    ngay_hien_tai = None
    for sk in body.events:
        if sk.name not in an.SU_KIEN_CHO_PHEP:
            continue
        await an.ghi_su_kien(db, body.anonymous_id, body.session_id, sk.name, sk.properties, sk.at)
        nhan += 1
        ngay_hien_tai = an.chuan_hoa_thoi_gian(sk.at).strftime("%Y-%m-%d")

    if nhan > 0 and ngay_hien_tai is not None:
        await an.xep_viec_tong_hop(db, ngay_hien_tai)
    return {"accepted": nhan, "filtered": None, "tracked_online_users": online}