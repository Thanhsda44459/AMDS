"""Read model dashboard: worker tổng hợp analytics_events thành số liệu giờ/ngày.

Kiến trúc hai tầng (ANA-004): `analytics_events` là dữ liệu thô chỉ ghi thêm,
mọi truy vấn dashboard đọc từ read model đã tổng hợp. Nhờ vậy dashboard không
quét bảng sự kiện và tốc độ không phụ thuộc lượng sự kiện.

Worker dùng **lease** thay vì cờ đơn giản: job có `lease_until`, ai cũng giành
được job quá hạn nên khi tiến trình chết giữa chừng thì việc vẫn được gán lại
thay vì kẹt vĩnh viễn (cùng ý với `QuanLyTasks.khoi_phuc` cho audio).

Tổng hợp dùng `replace` (xoá rồi ghi lại) nên chạy lại nhiều lần cho ra cùng
kết quả — không cộng dồn và không nhân đôi số liệu.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.db import get_database
from app.services.analytics_svc import khoa_su_kien
from app.services.presence import dem_online

# Job chạy tối đa 30 giây, quá hạn thì tiến trình khác giành lại.
HAN_THUE_GIAY = 30
# Chờ job tối thiểu 15 giây để gom nhiều sự kiện thành một lần tổng hợp.
CHU_KY_GIAY = 15
SO_NGAY_LUU = 30


async def _tong_hop_ngay(db, metric_date: str) -> dict:
    """Dựng lại toàn bộ số liệu của một ngày từ sự kiện thô."""
    gioi_han = datetime.strptime(metric_date, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
    truc = {"metric_date": metric_date, "occurred_at": {"$lt": gioi_han}}

    tong = {"views": 0, "audio_plays": 0, "searches": 0, "page_engaged": 0}
    theo_gio: dict[str, dict] = {}
    theo_poi: dict[str, dict] = {}
    theo_cum_tim: dict[str, int] = {}
    thiet_bi: set[str] = set()
    phien: set[str] = set()

    async for ev in db["analytics_events"].find(truc):
        ten = ev.get("name")
        gio = ev.get("metric_hour", 0)
        khoa_gio = khoa_su_kien(metric_date, gio)
        o = theo_gio.setdefault(khoa_gio, {"views": 0, "audio_plays": 0, "searches": 0})
        if ten == "page_viewed":
            tong["views"] += 1
            o["views"] += 1
        elif ten == "audio_played":
            tong["audio_plays"] += 1
            o["audio_plays"] += 1
        elif ten == "search":
            tong["searches"] += 1
            o["searches"] += 1
            cum = str(ev.get("properties", {}).get("query", "")).strip()[:120].lower()
            if cum:
                theo_cum_tim[cum] = theo_cum_tim.get(cum, 0) + 1
        elif ten == "page_engaged":
            tong["page_engaged"] += 1
        poi = ev.get("poi_id")
        if poi:
            p = theo_poi.setdefault(str(poi), {"views": 0, "audio_plays": 0})
            if ten == "page_viewed":
                p["views"] += 1
            elif ten == "audio_played":
                p["audio_plays"] += 1
        if ev.get("anonymous_id"):
            thiet_bi.add(ev["anonymous_id"])
        if ev.get("session_id"):
            phien.add(ev["session_id"])

    await db["analytics_daily"].replace_one(
        {"metric_date": metric_date},
        {
            "metric_date": metric_date,
            **tong,
            "devices": len(thiet_bi),
            "sessions": len(phien),
            "updated_at": datetime.now(UTC),
        },
        upsert=True,
    )
    await db["analytics_hourly"].delete_many({"metric_date": metric_date})
    if theo_gio:
        await db["analytics_hourly"].insert_many(
            [
                {
                    "bucket": k,
                    "metric_date": metric_date,
                    "metric_hour": int(k.rsplit("T", 1)[1]),
                    **so,
                    "updated_at": datetime.now(UTC),
                }
                for k, so in theo_gio.items()
            ]
        )
    await db["analytics_poi_daily"].delete_many({"metric_date": metric_date})
    if theo_poi:
        await db["analytics_poi_daily"].insert_many(
            [
                {"metric_date": metric_date, "poi_id": pid, **so, "updated_at": datetime.now(UTC)}
                for pid, so in theo_poi.items()
            ]
        )
    await db["analytics_searches"].delete_many({"metric_date": metric_date})
    if theo_cum_tim:
        await db["analytics_searches"].insert_many(
            [
                {"metric_date": metric_date, "query": q, "count": n}
                for q, n in theo_cum_tim.items()
            ]
        )
    return {**tong, "devices": len(thiet_bi), "sessions": len(phien), "hours": len(theo_gio)}


async def lease_job(db) -> dict | None:
    """Giành một job tổng hợp. Job quá hạn thì giành lại được, không kẹt."""
    now = datetime.now(UTC)
    return await db["analytics_jobs"].find_one_and_update(
        {
            "status": {"$in": ["queued", "running"]},
            "lease_until": {"$lte": now},
        },
        {
            "$set": {
                "status": "running",
                "lease_until": now + timedelta(seconds=HAN_THUE_GIAY),
                "updated_at": now,
            }
        },
        sort=[("metric_date", -1)],
        return_document=True,
    )


async def chay_ngay(db, metric_date: str) -> dict:
    """Tổng hợp một ngày rồi đánh dấu job xong. Dùng cả cho test."""
    ket_qua = await _tong_hop_ngay(db, metric_date)
    await db["analytics_jobs"].update_one(
        {"metric_date": metric_date},
        {"$set": {"status": "done", "updated_at": datetime.now(UTC)}},
    )
    return ket_qua


class AnalyticsWorker:
    """Vòng nền: giành job, tổng hợp, ngủ, lặp. Tự dừng khi app tắt."""

    def __init__(self, chu_ky_giay: int = CHU_KY_GIAY) -> None:
        self.chu_ky_giay = chu_ky_giay
        self.db = None
        self.dang_chay = False
        self._nhiem_vu: asyncio.Task | None = None

    def gan_db(self, db) -> None:
        self.db = db

    async def bat_dau(self) -> None:
        if self.dang_chay:
            return
        self.dang_chay = True
        self._nhiem_vu = asyncio.create_task(self._chay_forever())

    async def dung(self) -> None:
        self.dang_chay = False
        if self._nhiem_vu is not None:
            self._nhiem_vu.cancel()
            self._nhiem_vu = None

    async def _chay_forever(self) -> None:
        while self.dang_chay:
            try:
                job = await lease_job(self.db)
                if job is not None:
                    await _tong_hop_ngay(self.db, job["metric_date"])
                    await self.db["analytics_jobs"].update_one(
                        {"metric_date": job["metric_date"]},
                        {"$set": {"status": "done", "updated_at": datetime.now(UTC)}},
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[analytics] worker lỗi, thử lại: {exc}")
            await asyncio.sleep(self.chu_ky_giay)

    async def don_co(self) -> int:
        """Dọn read model cũ ngoài SO_NGAY_LUU để DB không phình vô hạn."""
        nguong = (datetime.now(UTC) - timedelta(days=SO_NGAY_LUU)).strftime("%Y-%m-%d")
        dem = 0
        for ten in ("analytics_events", "analytics_hourly", "analytics_poi_daily", "analytics_searches"):
            kq = await self.db[ten].delete_many({"metric_date": {"$lt": nguong}})
            dem += kq.deleted_count
        await self.db["analytics_daily"].delete_many({"metric_date": {"$lt": nguong}})
        return dem


analytics_worker = AnalyticsWorker()


async def thong_ke(db, metric_date: str, so_ngay: int = 7) -> dict:
    """Đọc read model cho dashboard: tổng hôm nay, chuỗi ngày, POI nổi bật."""
    hom_nay = await db["analytics_daily"].find_one({"metric_date": metric_date}) or {}
    chuoi = await (
        db["analytics_daily"]
        .find({"metric_date": {"$lte": metric_date}})
        .sort("metric_date", -1)
        .limit(so_ngay)
        .to_list(length=so_ngay)
    )
    top = await (
        db["analytics_poi_daily"]
        .find({"metric_date": metric_date})
        .sort("views", -1)
        .limit(5)
        .to_list(length=5)
    )
    ten_poi: dict[str, str] = {}
    for dong in top:
        oid = dong.get("poi_id")
        if oid is None:
            continue
        poi = await db["pois"].find_one({"_id": _doi_oid(oid)})
        ten_poi[str(oid)] = poi["name"] if poi else oid
    cum_tim = await (
        db["analytics_searches"]
        .find({"metric_date": metric_date})
        .sort("count", -1)
        .limit(5)
        .to_list(length=5)
    )
    online = await dem_online()
    return {
        "metric_date": metric_date,
        "today_views": hom_nay.get("views", 0),
        "audio_plays": hom_nay.get("audio_plays", 0),
        "searches": hom_nay.get("searches", 0),
        "page_engaged": hom_nay.get("page_engaged", 0),
        "devices_today": hom_nay.get("devices", 0),
        "sessions_today": hom_nay.get("sessions", 0),
        # None khi Redis tắt: hiển thị "không có số liệu" chứ không báo 0 sai.
        "tracked_online_users": online,
        "presence_available": online is not None,
        "top_pois": [
            {"poi_id": str(d["poi_id"]), "name": ten_poi.get(str(d["poi_id"]), ""), "views": d.get("views", 0), "audio_plays": d.get("audio_plays", 0)}
            for d in top
        ],
        "top_searches": [{"query": d["query"], "count": d["count"]} for d in cum_tim],
        "daily": [
            {"metric_date": d["metric_date"], "views": d.get("views", 0), "audio_plays": d.get("audio_plays", 0), "searches": d.get("searches", 0)}
            for d in reversed(chuoi)
        ],
    }


def _doi_oid(gia_tri: str):
    """Chuyển chuỗi sang ObjectId, rác thì trả None để bỏ qua tên POI."""
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        return ObjectId(gia_tri)
    except (InvalidId, TypeError):
        return None


async def tong_hop_ngay_hien_tai() -> dict:
    """Tiện cho script/test: tổng hợp ngày UTC hôm nay."""
    db = get_database()
    return await chay_ngay(db, datetime.now(UTC).strftime("%Y-%m-%d"))