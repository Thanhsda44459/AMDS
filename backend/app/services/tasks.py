"""Quản lý tác vụ sinh audio: tối đa 3 song song, bền trong Mongo, SSE, phục hồi."""

import asyncio
import uuid
from datetime import UTC, datetime


class QuanLyTasks:
    """Hàng đợi trong tiến trình + snapshot Mongo để restart không mất."""

    def __init__(self, toi_da: int = 3) -> None:
        self.toi_da = toi_da
        self._sem: asyncio.Semaphore | None = None
        self._sem_loop: asyncio.AbstractEventLoop | None = None
        self.db = None
        self.nguoi_nghe: set[asyncio.Queue] = set()

    def _lay_sem(self) -> asyncio.Semaphore:
        """Semaphore gắn với event loop đang chạy, dựng lại khi loop đổi.

        `asyncio.Semaphore` khóa vào loop đã tạo nó. Tạo ở `__init__` thì loop
        đầu tiên chiếm mãi semaphore, và mọi loop sau sẽ ném
        `bound to a different event loop` — app còn chạy được nhưng test suite
        thì hỏng, vì mỗi TestClient là một loop mới.
        """
        loop = asyncio.get_running_loop()
        if self._sem is None or self._sem_loop is not loop:
            self._sem = asyncio.Semaphore(self.toi_da)
            self._sem_loop = loop
        return self._sem

    def gan_db(self, db) -> None:
        self.db = db

    async def dam_bao_index(self) -> None:
        await self.db["audio_tasks"].create_index("updated_at", expireAfterSeconds=14 * 86400)

    async def xep_viec(self, poi_id: str, lang: str) -> str:
        task_id = uuid.uuid4().hex
        await self.db["audio_tasks"].insert_one(
            {
                "task_id": task_id,
                "poi_id": poi_id,
                "lang": lang,
                "status": "queued",
                "progress": 0,
                "updated_at": datetime.now(UTC),
            }
        )
        asyncio.create_task(self._chay(task_id))
        return task_id

    async def _chay(self, task_id: str) -> None:
        async with self._lay_sem():
            await self._doi_trang_thai(task_id, "running", 10)
            doc = await self.db["audio_tasks"].find_one({"task_id": task_id})
            if not doc:
                return
            from bson import ObjectId

            from app.services.audio_svc import hoan_tat_audio, tao_mp3_cached
            from app.services.localization import dich_va_luu

            try:
                while (await self._doc(task_id)).get("status") == "paused":
                    await self._cham(task_id)
                    await asyncio.sleep(1)
                if (await self._doc(task_id)).get("status") == "canceled":
                    return
                poi_id = ObjectId(doc["poi_id"])
                ban_dich = await self.db["poi_localizations"].find_one(
                    {"poi_id": poi_id, "lang": doc["lang"]}
                )
                if not ban_dich:
                    ban_dich = await dich_va_luu(self.db, poi_id, doc["lang"])
                await self._doi_trang_thai(task_id, "running", 50)
                tep, _hit = await tao_mp3_cached(ban_dich["description"] or ban_dich["name"], doc["lang"])
                from app.services.audio_svc import duong_audio_url

                url = duong_audio_url(tep.name, doc["lang"])
                await hoan_tat_audio(self.db, poi_id, doc["lang"], url)
                await self._doi_trang_thai(task_id, "done", 100)
            except Exception as exc:
                await self.db["audio_tasks"].update_one(
                    {"task_id": task_id},
                    {"$set": {"status": "error", "loi": str(exc)[:300], "updated_at": datetime.now(UTC)}},
                )
                await self._dang("error", task_id)

    async def _doc(self, task_id: str) -> dict:
        return await self.db["audio_tasks"].find_one({"task_id": task_id}) or {}

    async def _cham(self, task_id: str) -> None:
        await self.db["audio_tasks"].update_one(
            {"task_id": task_id}, {"$set": {"updated_at": datetime.now(UTC)}}
        )

    async def _doi_trang_thai(self, task_id: str, status: str, progress: int) -> None:
        await self.db["audio_tasks"].update_one(
            {"task_id": task_id},
            {"$set": {"status": status, "progress": progress, "updated_at": datetime.now(UTC)}},
        )
        await self._dang(status, task_id)

    async def _dang(self, status: str, task_id: str) -> None:
        for q in list(self.nguoi_nghe):
            try:
                q.put_nowait({"task_id": task_id, "status": status})
            except asyncio.QueueFull:
                pass

    async def dieu_khien(self, task_id: str, lenh: str) -> bool:
        doc = await self._doc(task_id)
        if not doc:
            return False
        if lenh == "pause" and doc["status"] in ("queued", "running"):
            await self._doi_trang_thai(task_id, "paused", doc.get("progress", 0))
        elif lenh == "resume" and doc["status"] == "paused":
            await self._doi_trang_thai(task_id, "queued", doc.get("progress", 0))
            asyncio.create_task(self._chay(task_id))
        elif lenh == "cancel":
            await self._doi_trang_thai(task_id, "canceled", doc.get("progress", 0))
        return True

    async def khoi_phuc(self) -> int:
        """Restart thì xếp lại việc treo quá 5 phút, coi như retryable."""
        nguong = datetime.now(UTC).timestamp() - 5 * 60
        dem = 0
        async for doc in self.db["audio_tasks"].find({"status": {"$in": ["running", "paused", "queued"]}}):
            ts = doc.get("updated_at")
            if ts and ts.timestamp() < nguong:
                await self._doi_trang_thai(doc["task_id"], "queued", 0)
                asyncio.create_task(self._chay(doc["task_id"]))
                dem += 1
        return dem


quan_ly_tasks = QuanLyTasks()
