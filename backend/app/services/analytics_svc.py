"""Analytics có consent: cổng đồng ý, chuẩn hóa sự kiện, ghi và xếp việc tổng hợp.

Nguyên tắc privacy-by-design (FR-80, NFR-30): **không có consent thì không ghi
gì cả**. Cổng consent gồm hai lớp độc lập:

1. `receipt` ký HMAC — client phải trình receipt còn hạn mà không thể tự chế ra.
2. `analytics_consents` trong Mongo — trạng thái do server giữ, client không sửa được.

Chỉ khi cả hai khớp thì sự kiện mới được ghi. Thu hồi consent làm `collect`
trả 403 ngay ở lần gọi kế tiếp, không cần xóa dữ liệu đã ghi.

Sự kiện chỉ mang `anonymous_id` + tên sự kiện + thuộc tính đã lọc. Không ghi
IP, không ghi tài khoản, không ghi hành trình: đó là lý do có `LY_DO_LO` bot
và `KHOA_CAM` chặn field nhận dạng.
"""

import base64
import hashlib
import hmac
import re
import time
from datetime import UTC, datetime, timedelta

from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.redis_client import lay_redis
from app.services.ratelimit import cho_phep

# Chỉ nhận sự kiện trong danh sách trắng, lạ thì bỏ chứ không tự động tạo metric.
SU_KIEN_CHO_PHEP = (
    "session_started",
    "page_viewed",
    "page_engaged",
    "search",
    "audio_played",
    "poi_viewed",
)

# Tên sự kiện nghi do bot/crawler — chặn để số liệu không bị bơm.
DAU_BOT = ("bot", "crawler", "spider", "headless", "curl", "wget", "python-requests", "postman")

# Thuộc tính nhận dạng cá nhân — không bao giờ lưu, kể cả client gửi lên.
KHOA_CAM = (
    "email",
    "phone",
    "cccd",
    "cmnd",
    "password",
    "matkhau",
    "token",
    "authorization",
    "cookie",
    "ip",
    "address",
    "ten_dang_nhap",
)

TOI_DA_THUOC_TINH = 8
TOI_DA_DO_DAI_CHUOI = 200
# Lệch giờ quá 1 ngày coi như rác, ghi bằng giờ server.
LECH_GIOI_HAN_GIAY = 86400

# Ngưỡng analytics ẩn danh: một thiết bị 60 lượt / 10 phút, một IP 600 lượt.
GIOI_HAN_ANON = 60
GIOI_HAN_IP = 600
CUA_SO_PHUT = 10

# Receipt sống 1 năm: đồng ý là quyết định dài hạn, hủy thì thu hồi ngay.
HAN_RECEIPT_NGAY = 365

MA_ANON = re.compile(r"^[a-zA-Z0-9_-]{16,64}$")


def hop_le(anonymous_id: str) -> bool:
    """anonymous_id là chuỗi ngẫu nhiên do client tự sinh, không phải định danh."""
    return bool(MA_ANON.match(anonymous_id or ""))


def _bimat() -> bytes:
    return settings.jwt_secret.encode()


def _noi_dung_receipt(anonymous_id: str, het_han: int) -> bytes:
    return f"{anonymous_id}|{het_han}".encode()


def lam_receipt(anonymous_id: str) -> str:
    """Cấp receipt chứng minh đã đồng ý. Ký HMAC nên client không giả mạo được."""
    het_han = int((datetime.now(UTC) + timedelta(days=HAN_RECEIPT_NGAY)).timestamp())
    chu_ky = hmac.new(_bimat(), _noi_dung_receipt(anonymous_id, het_han), hashlib.sha256).hexdigest()
    raw = base64.urlsafe_b64encode(f"{anonymous_id}|{het_han}|{chu_ky}".encode()).decode()
    return raw.rstrip("=")


def doc_receipt(receipt: str) -> dict | None:
    """Xác thực chữ ký và hạn. Sai định dạng, sai chữ ký hoặc hết hạn → None."""
    if not receipt or len(receipt) > 512:
        return None
    try:
        phuc = base64.urlsafe_b64decode(receipt + "=" * (-len(receipt) % 4)).decode()
        anonymous_id, het_han, chu_ky = phuc.split("|")
        het_han = int(het_han)
    except (ValueError, UnicodeDecodeError):
        return None
    ky_dung = hmac.new(_bimat(), _noi_dung_receipt(anonymous_id, het_han), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(ky_dung, chu_ky):
        return None
    if het_han < datetime.now(UTC).timestamp():
        return None
    return {"anonymous_id": anonymous_id, "het_han": het_han}


def ly_do_loc(user_agent: str) -> str | None:
    """Bot/crawler không phải khách thật — trả lý do để ghi log và bỏ qua."""
    ua = (user_agent or "").lower()
    for dau in DAU_BOT:
        if dau in ua:
            return f"bot:{dau}"
    return None


def chuan_hoa_thoi_gian(gia_tri: object) -> datetime:
    """Chuẩn hóa thời điểm client gửi; quá xa thời điểm server thì lấy giờ server."""
    if not isinstance(gia_tri, (int, float)) or isinstance(gia_tri, bool):
        return datetime.now(UTC)
    moc = datetime.fromtimestamp(gia_tri / 1000, tz=UTC)
    if abs((datetime.now(UTC) - moc).total_seconds()) > LECH_GIOI_HAN_GIAY:
        return datetime.now(UTC)
    return moc


def lam_sach(thuoc_tinh: object) -> dict:
    """Chỉ giữ giá trị vô hại và ngắn; bỏ field nhận dạng cá nhân."""
    if not isinstance(thuoc_tinh, dict):
        return {}
    ket_qua: dict = {}
    for khoa, gia_tri in list(thuoc_tinh.items())[:TOI_DA_THUOC_TINH]:
        ten = str(khoa)[:60]
        if ten.lower() in KHOA_CAM:
            continue
        if isinstance(gia_tri, bool) or isinstance(gia_tri, (int, float)):
            ket_qua[ten] = gia_tri
        elif isinstance(gia_tri, str):
            ket_qua[ten] = gia_tri[:TOI_DA_DO_DAI_CHUOI]
    return ket_qua


def khoa_su_kien(metric_date: str, metric_hour: int) -> str:
    """Khóa read model giờ: ngày + giờ, tổng hợp lại bằng replace nên idempotent."""
    return f"{metric_date}T{metric_hour:02d}"


async def dam_bao_index(db) -> None:
    """Index cho cả nhóm collection analytics_* (ANA-004)."""
    await db["analytics_consents"].create_index("anonymous_id", unique=True)
    await db["analytics_devices"].create_index("last_seen")
    await db["analytics_sessions"].create_index([("session_id", 1)], unique=True)
    await db["analytics_events"].create_index([("occurred_at", -1)])
    await db["analytics_events"].create_index([("metric_date", 1), ("metric_hour", 1)])
    await db["analytics_events"].create_index("poi_id")
    await db["analytics_jobs"].create_index([("status", 1), ("lease_until", 1)])
    # Một ngày chỉ có một job: hai request cùng lúc sẽ đua tạo, unique index
    # chặn giúp xep_viec_tong_hop chỉ cần xử lý DuplicateKeyError.
    await db["analytics_jobs"].create_index("metric_date", unique=True)
    # Job cũ xong rồi thì tự dọn, không phình vô hạn.
    await db["analytics_jobs"].create_index("updated_at", expireAfterSeconds=14 * 86400)


async def dat_consent(db, anonymous_id: str, granted: bool) -> None:
    """Server giữ trạng thái consent; client không sửa trực tiếp được."""
    trang_thai = "granted" if granted else "revoked"
    await db["analytics_consents"].update_one(
        {"anonymous_id": anonymous_id},
        {
            "$set": {"status": trang_thai, "updated_at": datetime.now(UTC)},
            "$setOnInsert": {"created_at": datetime.now(UTC)},
        },
        upsert=True,
    )


async def trang_thai_consent(db, anonymous_id: str) -> str:
    """`granted`, `revoked` hoặc `unknown` khi chưa từng chọn."""
    ban = await db["analytics_consents"].find_one({"anonymous_id": anonymous_id})
    return ban.get("status", "unknown") if ban else "unknown"


async def co_consent(db, anonymous_id: str) -> bool:
    return await trang_thai_consent(db, anonymous_id) == "granted"


async def cap_nhat_device(db, anonymous_id: str, user_agent: str) -> None:
    """Ghi nhận thiết bị ẩn danh — chỉ giữ dấu vết trình duyệt, không định danh."""
    gio = datetime.now(UTC)
    await db["analytics_devices"].update_one(
        {"anonymous_id": anonymous_id},
        {
            "$set": {"user_agent": user_agent[:200], "last_seen": gio},
            "$setOnInsert": {"first_seen": gio},
        },
        upsert=True,
    )


async def cap_nhat_session(db, anonymous_id: str, session_id: str, user_agent: str) -> None:
    """Ghi nhận phiên của thiết bị; `started_at` giữ nguyên qua các lần heartbeat.

    Đây là nơi tách *phiên* (mở app) khỏi *thiết bị* (anonymous_id): số phiên
    hôm nay và số thiết bị hôm nay là hai số khác nhau trên dashboard.
    """
    gio = datetime.now(UTC)
    await db["analytics_sessions"].update_one(
        {"session_id": session_id[:64]},
        {
            "$set": {
                "anonymous_id": anonymous_id,
                "last_seen": gio,
                "user_agent": user_agent[:200],
            },
            "$setOnInsert": {"started_at": gio},
        },
        upsert=True,
    )


async def ghi_su_kien(
    db,
    anonymous_id: str,
    session_id: str,
    ten: str,
    thuoc_tinh: object,
    thoi_diem: object,
) -> dict:
    """Ghi một sự kiện đã lọc, kèm khóa metric để worker tổng hợp theo giờ/ngày."""
    luc = chuan_hoa_thoi_gian(thoi_diem)
    sach = lam_sach(thuoc_tinh)
    metric_date = luc.strftime("%Y-%m-%d")
    metric_hour = luc.hour
    doc = {
        "anonymous_id": anonymous_id,
        "session_id": session_id[:64],
        "name": ten,
        "properties": sach,
        "poi_id": str(sach["poi_id"])[:24] if sach.get("poi_id") else None,
        "occurred_at": luc,
        "metric_date": metric_date,
        "metric_hour": metric_hour,
        "ingested_at": datetime.now(UTC),
    }
    await db["analytics_events"].insert_one(doc)
    return doc


async def xep_viec_tong_hop(db, metric_date: str) -> None:
    """Xếp, hoặc xếp lại, job tổng hợp cho một ngày.

    Job đang chạy thì không đụng để không phá vỡ lượt đang tổng hợp. Job đã
    `done` thì **phải xếp lại**: nếu không, sự kiện đến sau lần tổng hợp đầu
    tiên sẽ không bao giờ vào số liệu cho tới khi ngày đó trôi qua TTL.
    """
    gio = datetime.now(UTC)
    await db["analytics_jobs"].update_one(
        {"metric_date": metric_date, "status": "done"},
        {"$set": {"status": "queued", "lease_until": gio, "updated_at": gio}},
    )
    try:
        await db["analytics_jobs"].update_one(
            {"metric_date": metric_date},
            {
                "$setOnInsert": {
                    "status": "queued",
                    "lease_until": gio,
                    "updated_at": gio,
                }
            },
            upsert=True,
        )
    except DuplicateKeyError:
        # Hai request cùng lúc tạo job: index unique metric_date bắt được, coi
        # như đã có job là đúng.
        return


async def _dem_redis(redis, anonymous_id: str, ip: str) -> tuple[bool, int] | None:
    """Đếm lượt trong Redis, trả None khi Redis lỗi để lùi về Mongo."""
    moc = int(time.time() // (CUA_SO_PHUT * 60))
    try:
        for khoa, gioi_han in (
            (f"quan4:rl:anon:{anonymous_id}", GIOI_HAN_ANON),
            (f"quan4:rl:ip:{ip}", GIOI_HAN_IP),
        ):
            ten = f"{khoa}:{moc}"
            so = int(await redis.incr(ten))
            if so == 1:
                await redis.expire(ten, CUA_SO_PHUT * 120)
            if so > gioi_han:
                return False, CUA_SO_PHUT * 60
        return True, 0
    except Exception:
        return None


async def cho_phep_luong(db, anonymous_id: str, ip: str) -> tuple[bool, int]:
    """Ngưỡng analytics: 60 lượt/10 phút mỗi thiết bị, 600 lượt/10 phút mỗi IP.

    Redis đếm trước vì nhẹ và nhiều tiến trình cùng thấy một số; Redis tắt thì
    lùi về Mongo TTL thay vì mở cửa — thiếu chặn còn hơn không chặn.
    """
    redis = await lay_redis()
    if redis is not None:
        ket_qua = await _dem_redis(redis, anonymous_id, ip)
        if ket_qua is not None:
            return ket_qua
    ok, cho = await cho_phep(
        db, f"anon:{anonymous_id}", "analytics/collect", GIOI_HAN_ANON, CUA_SO_PHUT
    )
    if not ok:
        return False, cho
    ok, cho = await cho_phep(db, f"ip:{ip}", "analytics/collect", GIOI_HAN_IP, CUA_SO_PHUT)
    return (True, 0) if ok else (False, cho)