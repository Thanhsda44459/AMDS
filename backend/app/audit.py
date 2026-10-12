"""Ghi audit log cho thao tác quản trị, không ghi dữ liệu nhạy cảm."""

from datetime import UTC, datetime


async def ghi_audit(db, username: str, hanh_dong: str, tai_nguyen: str) -> None:
    """Ghi một dòng audit, chỉ giữ action/user/resource/timestamp."""
    await db["audit_logs"].insert_one(
        {
            "action": hanh_dong,
            "username": username,
            "resource": tai_nguyen,
            "timestamp": datetime.now(UTC),
        }
    )
