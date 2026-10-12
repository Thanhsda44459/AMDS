"""Route quản trị POI: tạo, sửa, xóa. Mọi route đòi đăng nhập."""

from datetime import UTC, datetime

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.audit import ghi_audit
from app.auth import doi_quyen
from app.db import get_database
from app.routers.poi import doi_poi
from app.services.sync import cham_dataset, ghi_mo_xoa

router = APIRouter(prefix="/admin/pois", tags=["admin-poi"])

DuocTaoPoi = doi_quyen("poi:create")
DuocSuaPoi = doi_quyen("poi:update")
DuocXoaPoi = doi_quyen("poi:delete")


class PoiNhap(BaseModel):
    """Dữ liệu admin nhập khi tạo/sửa, validate ở biên (POI-010)."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    trigger_radius: float = Field(default=30, ge=5, le=200)
    audio_priority: int = Field(default=0, ge=0, le=100)


def doi_id(poi_id: str) -> ObjectId:
    """Đổi chuỗi thành ObjectId, rác thì 400 chứ không 500."""
    try:
        return ObjectId(poi_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Id không đúng định dạng") from None


@router.post("", status_code=201, summary="Tạo POI")
async def tao_poi(body: PoiNhap, user: dict = DuocTaoPoi) -> dict:
    db = get_database()
    du_lieu = body.model_dump()
    du_lieu.update(
        {
            "is_active": False,
            "audio_status": "processing",
            "activation_requested": True,
            "updated_at": datetime.now(UTC),
            "version": await cham_dataset(db),
        }
    )
    ket_qua = await db["pois"].insert_one(du_lieu)
    doc = await db["pois"].find_one({"_id": ket_qua.inserted_id})
    assert doc is not None
    await ghi_audit(db, user["username"], "poi:create", f"poi:{ket_qua.inserted_id}")
    from app.services.audio_svc import kich_hoat_sinh_audio

    await kich_hoat_sinh_audio(db, ket_qua.inserted_id)
    return doi_poi(doc)


@router.put("/{poi_id}", summary="Sửa POI")
async def sua_poi(poi_id: str, body: PoiNhap, user: dict = DuocSuaPoi) -> dict:
    db = get_database()
    oid = doi_id(poi_id)
    cu = await db["pois"].find_one({"_id": oid})
    if cu is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    du_lieu_sua = body.model_dump()
    du_lieu_sua["updated_at"] = datetime.now(UTC)
    ket_qua = await db["pois"].update_one({"_id": oid}, {"$set": du_lieu_sua})
    if ket_qua.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    # Mô tả đổi thì sinh lại audio, tạm ẩn chờ tiếng Anh.
    if body.description != cu.get("description", "") or body.name != cu.get("name", ""):
        from app.services.audio_svc import kich_hoat_sinh_audio

        await kich_hoat_sinh_audio(db, oid)
    await db["pois"].update_one({"_id": oid}, {"$set": {"version": await cham_dataset(db)}})
    doc = await db["pois"].find_one({"_id": oid})
    assert doc is not None
    await ghi_audit(db, user["username"], "poi:update", f"poi:{poi_id}")
    return doi_poi(doc)


@router.delete("/{poi_id}", status_code=204, summary="Xóa POI")
async def xoa_poi(poi_id: str, user: dict = DuocXoaPoi) -> Response:
    db = get_database()
    oid = doi_id(poi_id)
    ket_qua = await db["pois"].delete_one({"_id": oid})
    if ket_qua.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    # Dọn bản dịch liên quan, chưa transaction (cần replica set, PROD-004).
    await db["poi_localizations"].delete_many({"poi_id": oid})
    phien_ban = await cham_dataset(db)
    await ghi_mo_xoa(db, oid, phien_ban)
    await ghi_audit(db, user["username"], "poi:delete", f"poi:{poi_id}")
    return Response(status_code=204)
