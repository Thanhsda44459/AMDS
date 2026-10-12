"""Luồng chủ quán: đăng ký, duyệt, submission, thông báo, cổng xác minh."""

from datetime import UTC, datetime

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.audit import ghi_audit
from app.auth import YeuCauDangNhap, YeuCauOwnerDuyet, bam_mat_khau, doi_quyen
from app.db import get_database
from app.pii import giai_ma_pii, ma_hoa_pii
from app.services.sync import cham_dataset

router = APIRouter(tags=["owner"])

DuocQuanLyUser = doi_quyen("user:update")
DuocDuyetPoi = doi_quyen("poi:approve")


class DangKyOwner(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    cccd: str = Field(min_length=9, max_length=20)


class XetDuyet(BaseModel):
    admin_note: str = ""


class SubmissionNhap(BaseModel):
    poi_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


def doi_id(poi_id: str) -> ObjectId:
    try:
        return ObjectId(poi_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None


@router.post("/owner/register", summary="Đăng ký làm chủ quán")
async def dang_ky(body: DangKyOwner) -> dict:
    db = get_database()
    if await db["admin_users"].find_one({"username": body.username}):
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã dùng")
    ma_cccd = ma_hoa_pii(body.cccd)
    if ma_cccd is None:
        raise HTTPException(status_code=500, detail="Chưa cấu hình mã hóa PII")
    await db["admin_users"].insert_one(
        {
            "username": body.username,
            "password_hash": bam_mat_khau(body.password),
            "role": "poi_owner",
            "is_verified": False,
            "is_poi_owner_verified": False,
            "cccd_encrypted": ma_cccd,
            "pii_created_at": datetime.now(UTC),
            "pii_masked": False,
            "created_at": datetime.now(UTC),
        }
    )
    await db["owner_registrations"].insert_one(
        {"username": body.username, "status": "pending", "admin_note": "", "created_at": datetime.now(UTC)}
    )
    return {"ok": True, "status": "pending"}


@router.get("/owner/registration-status", summary="Xem trạng thái duyệt")
async def xem_trang_thai(user: dict = YeuCauDangNhap) -> dict:
    don = await get_database()["owner_registrations"].find_one({"username": user["username"]})
    if not don:
        raise HTTPException(status_code=404, detail="Chưa đăng ký")
    return {"status": don["status"], "admin_note": don.get("admin_note", "")}


@router.get("/owner/registrations", summary="Liệt kê đơn chờ duyệt")
async def liet_ke_don(user: dict = DuocQuanLyUser) -> list[dict]:
    docs = await get_database()["owner_registrations"].find({"status": "pending"}).to_list(length=100)
    return [{"username": d["username"], "status": d["status"]} for d in docs]


@router.post("/owner/registrations/{username}/approve", summary="Duyệt chủ quán")
async def duyet(user_duyet: dict = DuocQuanLyUser, username: str = "") -> dict:
    db = get_database()
    don = await db["owner_registrations"].find_one({"username": username, "status": "pending"})
    if not don:
        raise HTTPException(status_code=404, detail="Không có đơn chờ")
    await db["owner_registrations"].update_one({"username": username}, {"$set": {"status": "approved"}})
    await db["admin_users"].update_one(
        {"username": username}, {"$set": {"is_verified": True, "is_poi_owner_verified": True}}
    )
    await ghi_audit(db, user_duyet["username"], "owner:approve", f"owner:{username}")
    return {"ok": True}


@router.post("/owner/registrations/{username}/reject", summary="Từ chối đơn")
async def tu_choi(body: XetDuyet, user_duyet: dict = DuocQuanLyUser, username: str = "") -> dict:
    if not body.admin_note.strip():
        raise HTTPException(status_code=400, detail="Từ chối phải có ghi chú")
    db = get_database()
    don = await db["owner_registrations"].find_one({"username": username, "status": "pending"})
    if not don:
        raise HTTPException(status_code=404, detail="Không có đơn chờ")
    await db["owner_registrations"].update_one(
        {"username": username}, {"$set": {"status": "rejected", "admin_note": body.admin_note}}
    )
    await ghi_audit(db, user_duyet["username"], "owner:reject", f"owner:{username}")
    return {"ok": True}


@router.post("/owner/submissions", summary="Gửi tạo/sửa POI chờ duyệt")
async def gui_submission(body: SubmissionNhap, user: dict = YeuCauOwnerDuyet) -> dict:
    db = get_database()
    if body.poi_id:
        poi = await db["pois"].find_one({"_id": doi_id(body.poi_id)})
        if not poi:
            raise HTTPException(status_code=404, detail="Không tìm thấy POI")
        if poi.get("owner_username") and poi["owner_username"] != user["username"]:
            raise HTTPException(status_code=403, detail="Không phải quán của bạn")
    ket_qua = await db["owner_submissions"].insert_one(
        {
            "username": user["username"],
            "poi_id": body.poi_id,
            "data": {"name": body.name, "description": body.description, "lat": body.lat, "lng": body.lng},
            "status": "pending",
            "created_at": datetime.now(UTC),
        }
    )
    return {"ok": True, "submission_id": str(ket_qua.inserted_id)}


@router.get("/owner/submissions/mine", summary="Submission của tôi")
async def submission_cua_toi(user: dict = YeuCauOwnerDuyet) -> list[dict]:
    docs = await get_database()["owner_submissions"].find({"username": user["username"]}).to_list(length=100)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@router.post("/owner/submissions/{sid}/approve", summary="Duyệt submission vào POI")
async def duyet_submission(sid: str, user_duyet: dict = DuocDuyetPoi) -> dict:
    db = get_database()
    try:
        oid = ObjectId(sid)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None
    sub = await db["owner_submissions"].find_one({"_id": oid, "status": "pending"})
    if not sub:
        raise HTTPException(status_code=404, detail="Không có submission chờ")
    du_lieu = dict(sub["data"])
    du_lieu.update(
        {
            "is_active": False,
            "audio_status": "processing",
            "activation_requested": True,
            "updated_at": datetime.now(UTC),
            "version": await cham_dataset(db),
        }
    )
    if sub.get("poi_id"):
        poi_oid = doi_id(sub["poi_id"])
        await db["pois"].update_one({"_id": poi_oid}, {"$set": du_lieu})
        poi_id = poi_oid
    else:
        du_lieu["owner_username"] = sub["username"]
        poi_id = (await db["pois"].insert_one(du_lieu)).inserted_id
    await db["owner_submissions"].update_one({"_id": oid}, {"$set": {"status": "approved"}})
    await db["owner_notifications"].insert_one(
        {"username": sub["username"], "message": f"Đề xuất cho '{du_lieu['name']}' đã được duyệt", "read": False, "created_at": datetime.now(UTC)}
    )
    from app.services.audio_svc import kich_hoat_sinh_audio

    await kich_hoat_sinh_audio(db, poi_id)
    await ghi_audit(db, user_duyet["username"], "poi:approve", f"submission:{sid}")
    return {"ok": True, "poi_id": str(poi_id)}


@router.get("/owner/submissions/pending", summary="Submission chờ duyệt (admin)")
async def submission_cho_duyet(user_duyet: dict = DuocDuyetPoi) -> list[dict]:
    """Hàng đợi duyệt cho admin.

    Không có endpoint này thì admin không biết có quán nào đang chờ: mỗi chủ
    quán chỉ thấy submission của chính họ qua `/mine`.
    """
    docs = await get_database()["owner_submissions"].find({"status": "pending"}).to_list(length=100)
    return [
        {
            "id": str(d["_id"]),
            "username": d["username"],
            "name": d.get("data", {}).get("name", ""),
            "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
        }
        for d in docs
    ]


@router.get("/owner/notifications", summary="Thông báo của tôi")
async def thong_bao(user: dict = YeuCauOwnerDuyet) -> list[dict]:
    docs = await get_database()["owner_notifications"].find({"username": user["username"]}).sort("created_at", -1).to_list(length=50)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@router.post("/owner/notifications/{nid}/read", summary="Đánh dấu đã đọc")
async def da_doc(nid: str, user: dict = YeuCauOwnerDuyet) -> dict:
    try:
        oid = ObjectId(nid)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None
    await get_database()["owner_notifications"].update_one(
        {"_id": oid, "username": user["username"]}, {"$set": {"read": True}}
    )
    return {"ok": True}


async def che_pii_cu(db, gio_hien_tai: datetime) -> int:
    """Che PII quá 180 ngày, data minimization, test được bằng đồng hồ giả."""
    nguong = gio_hien_tai.timestamp() - 180 * 86400
    dem = 0
    async for user in db["admin_users"].find({"pii_masked": {"$ne": True}, "cccd_encrypted": {"$ne": None}}):
        created = user.get("pii_created_at")
        if created and created.timestamp() < nguong:
            await db["admin_users"].update_one(
                {"_id": user["_id"]}, {"$set": {"cccd_encrypted": None, "pii_masked": True}}
            )
            dem += 1
    return dem


async def doc_cccd(username: str) -> str | None:
    """Đọc CCCD khi thật sự cần, lỗi trả None."""
    user = await get_database()["admin_users"].find_one({"username": username})
    if not user:
        return None
    return giai_ma_pii(user.get("cccd_encrypted"))
