"""Xác thực: băm mật khẩu, JWT, dependency đọc phiên từ cookie hoặc Bearer."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Request

from app.config import settings
from app.db import get_database

ACCESS_PHUT = 30
REFRESH_NGAY = 7


def bam_mat_khau(mat_khau: str) -> str:
    """Băm bcrypt kèm salt ngẫu nhiên, hai lần băm cho hai chuỗi khác nhau."""
    return bcrypt.hashpw(mat_khau.encode(), bcrypt.gensalt()).decode()


def dung_mat_khau(mat_khau: str, bam: str) -> bool:
    """So khớp, sai băm thì trả False thay vì ném lỗi."""
    try:
        return bcrypt.checkpw(mat_khau.encode(), bam.encode())
    except ValueError:
        return False


def tao_token(username: str, role: str, loai: str, quyen: list[str] | None = None) -> str:
    """Cấp JWT access (30 phút) hoặc refresh (7 ngày), kèm danh sách quyền."""
    han = timedelta(minutes=ACCESS_PHUT) if loai == "access" else timedelta(days=REFRESH_NGAY)
    bi_mat = settings.jwt_secret if loai == "access" else settings.refresh_secret
    return jwt.encode(
        {"sub": username, "role": role, "permissions": quyen or [], "type": loai, "exp": datetime.now(UTC) + han},
        bi_mat,
        algorithm="HS256",
    )


def doc_token(token: str, loai: str) -> dict:
    """Kiểm chữ ký và hạn, sai thì 401 không lộ chi tiết."""
    bi_mat = settings.jwt_secret if loai == "access" else settings.refresh_secret
    try:
        data = jwt.decode(token, bi_mat, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Phiên không hợp lệ") from None
    if data.get("type") != loai:
        raise HTTPException(status_code=401, detail="Phiên không hợp lệ")
    return data


async def lay_user_theo_ten(username: str) -> dict | None:
    """Tìm user trong collection admin_users."""
    return await get_database()["admin_users"].find_one({"username": username})


async def quyen_hien_tai(username: str, role: str, token_quyen: list[str]) -> list[str]:
    """Quyền trong JWT để khỏi truy vấn DB; thiếu thì đọc role từ DB."""
    if token_quyen:
        return token_quyen
    from app.permissions import quyen_cua_role

    return await quyen_cua_role(get_database(), role)


async def lay_user_hien_tai(
    request: Request,
    access_token: str | None = Cookie(default=None),
) -> dict:
    """Đọc phiên từ cookie httpOnly, vẫn nhận Bearer để tương thích."""
    token = access_token
    if token is None:
        bearer = request.headers.get("Authorization", "")
        if bearer.startswith("Bearer "):
            token = bearer[7:]
    if token is None:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    data = doc_token(token, "access")
    user = await lay_user_theo_ten(str(data["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Phiên không hợp lệ")
    role = user.get("role", "admin")
    quyen = await quyen_hien_tai(user["username"], role, list(data.get("permissions", [])))
    return {"username": user["username"], "role": role, "permissions": quyen}


YeuCauDangNhap = Depends(lay_user_hien_tai)


def doi_quyen(ten_quyen: str):
    """Bảo vệ route theo quyền chi tiết, thiếu quyền trả 403."""

    async def kiem(user: dict = YeuCauDangNhap) -> dict:
        if ten_quyen not in user.get("permissions", []):
            raise HTTPException(status_code=403, detail="Không đủ quyền")
        return user

    return Depends(kiem)


async def doi_owner_da_duyet(user: dict = YeuCauDangNhap) -> dict:
    """Owner chưa duyệt gọi API nghiệp vụ thì 403, không chỉ ẩn nút."""
    if user.get("role") == "poi_owner":
        doc = await lay_user_theo_ten(user["username"])
        if not doc or not doc.get("is_poi_owner_verified"):
            raise HTTPException(status_code=403, detail="Tài khoản chủ quán chưa được duyệt")
    return user


YeuCauOwnerDuyet = Depends(doi_owner_da_duyet)


async def lay_user_refresh(
    request: Request,
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Đọc phiên refresh từ cookie để cấp access mới."""
    token = refresh_token
    if token is None:
        bearer = request.headers.get("Authorization", "")
        if bearer.startswith("Bearer "):
            token = bearer[7:]
    if token is None:
        raise HTTPException(status_code=401, detail="Phiên không hợp lệ")
    data = doc_token(token, "refresh")
    user = await lay_user_theo_ten(str(data["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Phiên không hợp lệ")
    return {"username": user["username"], "role": user.get("role", "admin")}


YeuCauRefresh = Depends(lay_user_refresh)
