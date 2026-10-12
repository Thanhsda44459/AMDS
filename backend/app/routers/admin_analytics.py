"""Số liệu cho Admin Dashboard: tổng quan analytics + cửa sổ quan sát runtime.

Đọc từ read model (`analytics_daily`, `analytics_hourly`, ...) chứ không quét
`analytics_events`, nên độ trễ không tăng theo lượng sự kiện. Hai nhóm số liệu
tách bạch: analytics chỉ có dữ liệu của thiết bị đã consent, còn cửa sổ runtime
là chẩn đoán vận hành và không phụ thuộc consent.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.auth import doi_quyen
from app.db import get_database
from app.services import runtime_observability as ro
from app.services.analytics_read import thong_ke

router = APIRouter(prefix="/admin", tags=["admin-analytics"])

# Cả hai nhóm số liệu đều đòi cùng một quyền xem analytics.
DuocXemAnalytics = doi_quyen("analytics:view")

CUA_SO_RUNTIME = ("24h", "7d")


@router.get("/analytics/summary", summary="Tổng quan analytics hôm nay")
async def tong_quan(ngay: str | None = None, so_ngay: int = 7, _user: dict = DuocXemAnalytics) -> dict:
    db = get_database()
    metric_date = ngay or datetime.now(UTC).strftime("%Y-%m-%d")
    so_ngay = max(1, min(so_ngay, 30))
    return await thong_ke(db, metric_date, so_ngay)


@router.get("/runtime-observability/location", summary="Cửa sổ quan sát vị trí runtime")
async def cua_so_runtime(window: str = "24h", _user: dict = DuocXemAnalytics) -> dict:
    if window not in CUA_SO_RUNTIME:
        window = "24h"
    return await ro.doc_cua_so(get_database(), window)