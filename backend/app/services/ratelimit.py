"""Giới hạn tần suất dùng chung bằng Mongo TTL: 30 yêu cầu mỗi 10 phút."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request

GIOI_HAN = 30
CUA_SO_PHUT = 10


async def dam_bao_index_ratelimit(db) -> None:
    await db["rate_limits"].create_index("het_han", expireAfterSeconds=0)


def khoa_cho(request: Request, user: dict | None = None) -> str:
    """Đếm theo user đăng nhập, ẩn danh thì theo IP."""
    if user and user.get("username"):
        return f"user:{user['username']}"
    ip = request.client.host if request.client else "la"
    return f"ip:{ip}"


def _giay_cho_lai(cu: dict, cua_so_phut: int) -> int:
    """Còn bao lâu nữa thì lượt cũ trượt khỏi cửa sổ, tối thiểu 1 giây."""
    luc = cu.get("luc")
    if luc is None:
        return cua_so_phut * 60
    # Mongo trả naive UTC nên so bằng now naive cho đồng nhất.
    moc_cu = luc.replace(tzinfo=None) if luc.tzinfo else luc
    con_lai = (moc_cu + timedelta(minutes=cua_so_phut) - datetime.now(UTC).replace(tzinfo=None)).total_seconds()
    return max(1, int(con_lai))


async def cho_phep(
    db,
    khoa: str,
    duong_dan: str,
    gioi_han: int = GIOI_HAN,
    cua_so_phut: int = CUA_SO_PHUT,
) -> tuple[bool, int]:
    """Đếm lượt trong cửa sổ trượt rồi ghi nhận. Trả (cho phép, giây phải chờ).

    Dùng chung cho audio, on-demand, analytics và quan sát runtime nên
    ngưỡng khác nhau chỉ việc truyền tham số, không nhân bản logic.
    """
    await dam_bao_index_ratelimit(db)
    moc = datetime.now(UTC) - timedelta(minutes=cua_so_phut)
    quy = {"khoa": khoa, "duong_dan": duong_dan, "luc": {"$gte": moc}}
    dem = await db["rate_limits"].count_documents(quy)
    if dem >= gioi_han:
        cu = await db["rate_limits"].find(quy).sort("luc", 1).limit(1).to_list(length=1)
        return False, _giay_cho_lai(cu[0], cua_so_phut) if cu else cua_so_phut * 60
    await db["rate_limits"].insert_one(
        {
            "khoa": khoa,
            "duong_dan": duong_dan,
            "luc": datetime.now(UTC),
            "het_han": datetime.now(UTC) + timedelta(minutes=cua_so_phut),
        }
    )
    return True, 0


async def kiem_tra(db, khoa: str, duong_dan: str) -> None:
    """Quá ngưỡng thì 429 kèm Retry-After, hai tiến trình vẫn đếm đúng."""
    ok, cho = await cho_phep(db, khoa, duong_dan)
    if not ok:
        raise HTTPException(
            status_code=429, detail="Quá nhiều yêu cầu, thử lại sau", headers={"Retry-After": str(cho)}
        )
