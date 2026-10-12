"""Route xác thực admin: login, me, refresh, logout."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.auth import (
    ACCESS_PHUT,
    REFRESH_NGAY,
    YeuCauDangNhap,
    YeuCauRefresh,
    bam_mat_khau,
    dung_mat_khau,
    lay_user_theo_ten,
    tao_token,
)
from app.config import la_dev

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])

THONG_BAO_SAI = "Sai tên đăng nhập hoặc mật khẩu"


class DangNhap(BaseModel):
    username: str
    password: str


def dat_cookie(response: Response, ten: str, token: str, tuoi_giay: int) -> None:
    """Cookie httpOnly, JS không đọc được để chống XSS lấy phiên."""
    response.set_cookie(
        ten,
        token,
        max_age=tuoi_giay,
        httponly=True,
        samesite="lax",
        secure=not la_dev(),
        path="/",
    )


@router.post("/login", summary="Đăng nhập admin")
async def dang_nhap(body: DangNhap, response: Response) -> dict:
    user = await lay_user_theo_ten(body.username)
    # Sai tên và sai mật khẩu trả cùng một thông báo để chống dò tài khoản.
    dung = (
        dung_mat_khau(body.password, user["password_hash"])
        if user
        else dung_mat_khau("gia", bam_mat_khau("gia"))
    )
    if user is None or not dung:
        raise HTTPException(status_code=401, detail=THONG_BAO_SAI)
    role = user.get("role", "admin")
    from app.db import get_database
    from app.permissions import quyen_cua_role

    quyen = await quyen_cua_role(get_database(), role)
    dat_cookie(
        response,
        "access_token",
        tao_token(user["username"], role, "access", quyen),
        ACCESS_PHUT * 60,
    )
    dat_cookie(
        response,
        "refresh_token",
        tao_token(user["username"], role, "refresh", quyen),
        REFRESH_NGAY * 86400,
    )
    return {"ok": True, "username": user["username"], "role": role}


@router.get("/me", summary="Xem phiên hiện tại")
async def xem_toi(user: dict = YeuCauDangNhap) -> dict:
    return user


@router.post("/refresh", summary="Cấp access mới từ refresh cookie")
async def lam_moi(response: Response, user: dict = YeuCauRefresh) -> dict:
    dat_cookie(
        response,
        "access_token",
        tao_token(user["username"], user["role"], "access", user.get("permissions", [])),
        ACCESS_PHUT * 60,
    )
    return {"ok": True}


@router.post("/logout", summary="Đăng xuất")
async def dang_xuat(response: Response) -> dict:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}
