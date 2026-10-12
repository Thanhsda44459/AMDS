"""Xem roles và audit logs, đòi quyền chi tiết."""

from fastapi import APIRouter

from app.auth import doi_quyen
from app.db import get_database

router = APIRouter(prefix="/admin", tags=["admin-quan-tri"])

DuocXemRole = doi_quyen("role:read")
DuocXemAudit = doi_quyen("audit:read")


@router.get("/roles", summary="Liệt kê roles")
async def liet_ke_roles(_user: dict = DuocXemRole) -> list[dict]:
    docs = await get_database()["roles"].find().to_list(length=50)
    return [
        {"name": d["name"], "priority": d.get("priority"), "permissions": d.get("permissions", [])}
        for d in docs
    ]


@router.get("/audit-logs", summary="Xem audit log")
async def xem_audit(_user: dict = DuocXemAudit) -> list[dict]:
    docs = await get_database()["audit_logs"].find().sort("timestamp", -1).to_list(length=100)
    for d in docs:
        d.pop("_id", None)
        ts = d.get("timestamp")
        d["timestamp"] = ts.isoformat() if ts else None
    return docs
