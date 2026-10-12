"""Quan sát vị trí runtime: kênh TÁCH RIÊNG khỏi analytics (FR-82, ANA-005).

Vì sao tách? Analytics phục vụ **quyết định kinh doanh** nên phải qua consent.
Kênh này phục vụ **chẩn đoán vận hành** (GPS có hoạt động không, độ chính xác
bao nhiêu, có bị từ chối quyền không) nên không được đi qua consent — trộn vào
sẽ hoặc làm hỏng ranh giới riêng tư, hoặc biến chẩn đoán thành theo dõi.

Bốn ràng buộc bắt buộc, mất ràng buộc nào cũng là lỗ hổng:

1. Chỉ nhận origin đã khai báo — chặn việc trang khác gọi chéo vào.
2. Rate limit riêng: 60 lượt/phút theo IP, 20 lượt/phút theo phiên.
3. Payload tối đa 16 KiB — chặn dồn dữ liệu hàng loạt.
4. **Bỏ mọi trường môi trường client gửi kèm** — không tin thiết bị về việc
   nó đang chạy ở môi trường nào; môi trường do server tự quyết.

Tọa độ được gom theo cửa sổ giờ và làm tròn, không lưu đường đi từng điểm.
"""

from datetime import UTC, datetime, timedelta

from app.services.ratelimit import cho_phep

# 16 KiB: đủ cho một lô mẫu vị trí, không đủ để dồn dữ liệu hàng loạt.
TOI_DA_THANH_TICH_KB = 16
KICH_THUOC_TOI_DA = TOI_DA_THANH_TICH_KB * 1024

GIOI_HAN_IP_MOT_PHUT = 60
GIOI_HAN_PHIEN_MOT_PHUT = 20

# Làm tròn tọa độ 3 chữ số thập phân (~110m) để không tái dựng hành trình.
DO_CHINH_XAC_TOA_DO = 3
SO_MAU_TOI_DA = 120


def kich_thuoc_than(json_bytes: bytes) -> int:
    """Kích thước thô của payload đã đọc, dùng cho kiểm tra 16 KiB."""
    return len(json_bytes)


def lam_sach_mau(mau: dict) -> dict | None:
    """Chỉ giữ lat/lng/accuracy/outcome/at, bỏ mọi trường client tự thêm."""
    if not isinstance(mau, dict):
        return None
    try:
        lat = round(float(mau["lat"]), DO_CHINH_XAC_TOA_DO)
        lng = round(float(mau["lng"]), DO_CHINH_XAC_TOA_DO)
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    do_chinh_xac = mau.get("accuracy")
    ket_qua = {
        "lat": lat,
        "lng": lng,
        "outcome": str(mau.get("outcome", "ok"))[:20],
    }
    if isinstance(do_chinh_xac, (int, float)) and not isinstance(do_chinh_xac, bool):
        ket_qua["accuracy"] = min(round(float(do_chinh_xac), 1), 100000)
    return ket_qua


async def dam_bao_index(db) -> None:
    """Index cho read model runtime, gọi ở Tầng 4 lúc khởi động."""
    await db["runtime_location_hourly"].create_index([("window_start", -1), ("cell", 1)], unique=True)


async def ghi_vi_tri(db, mau: list[dict]) -> int:
    """Gom mẫu vào bucket theo giờ. Bucket chỉ đếm số lần, không lưu hành trình."""
    moc = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    dem = 0
    for mau_sach in mau:
        if mau_sach is None:
            continue
        lat = mau_sach["lat"]
        lng = mau_sach["lng"]
        cell = f"{lat:.{DO_CHINH_XAC_TOA_DO}f},{lng:.{DO_CHINH_XAC_TOA_DO}f}"
        await db["runtime_location_hourly"].update_one(
            {"window_start": moc, "cell": cell},
            {
                "$inc": {"samples": 1, f"outcomes.{mau_sach['outcome']}": 1},
                "$set": {"updated_at": datetime.now(UTC)},
            },
            upsert=True,
        )
        dem += 1
    return dem


async def kiem_tra_tan_suat(db, ip: str, session_id: str) -> tuple[bool, int]:
    """Hai ngưỡng độc lập: theo IP và theo phiên, cùng dùng shared-state."""
    theo_ip, cho_ip = await cho_phep(
        db, f"ip:{ip}", "runtime-observability/location", GIOI_HAN_IP_MOT_PHUT, 1
    )
    if not theo_ip:
        return False, cho_ip
    theo_phien, cho_phien = await cho_phep(
        db, f"phien:{session_id}", "runtime-observability/location", GIOI_HAN_PHIEN_MOT_PHUT, 1
    )
    if not theo_phien:
        return False, cho_phien
    return True, 0


async def doc_cua_so(db, window: str = "24h") -> dict:
    """Đọc bucket trong cửa sổ 24h hoặc 7d cho màn hình quan sát của admin."""
    gio = 24 if window == "24h" else 7 * 24
    moc = datetime.now(UTC) - timedelta(hours=gio)
    tong = await db["runtime_location_hourly"].aggregate(
        [
            {"$match": {"window_start": {"$gte": moc}}},
            {"$group": {"_id": None, "samples": {"$sum": "$samples"}, "cells": {"$sum": 1}}},
        ]
    ).to_list(length=1)
    theo_outcome: dict[str, int] = {}
    async for dong in db["runtime_location_hourly"].find({"window_start": {"$gte": moc}}):
        for ten, so in (dong.get("outcomes") or {}).items():
            theo_outcome[ten] = theo_outcome.get(ten, 0) + int(so)
    diem = tong[0] if tong else {"samples": 0, "cells": 0}
    return {
        "window": window,
        "hours": gio,
        "samples": diem.get("samples", 0),
        "cells": diem.get("cells", 0),
        "outcomes": theo_outcome,
    }