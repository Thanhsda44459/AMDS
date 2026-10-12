"""Mã hóa PII (CCCD) bằng Fernet, lưu dạng v1 + mã, lỗi trả None."""

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def lay_khoa() -> Fernet | None:
    """Không có key cấu hình thì bỏ qua mã hóa chứ không crash."""
    if not settings.pii_key:
        return None
    return Fernet(settings.pii_key.encode())


def ma_hoa_pii(gia_tri: str) -> str | None:
    """Mã hóa, thất bại hoặc thiếu key thì None để caller xử lý."""
    khoa = lay_khoa()
    if khoa is None:
        return None
    return "v1:" + khoa.encrypt(gia_tri.encode()).decode()


def giai_ma_pii(ban_ma: str | None) -> str | None:
    """Giải mã, sai key hoặc hỏng thì None, không bao giờ lộ nội dung."""
    if not ban_ma or not ban_ma.startswith("v1:"):
        return None
    khoa = lay_khoa()
    if khoa is None:
        return None
    try:
        return khoa.decrypt(ban_ma[3:].encode()).decode()
    except InvalidToken:
        return None
