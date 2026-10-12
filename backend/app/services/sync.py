"""Phiên bản dataset cho delta sync: mọi ghi POI đều chạm phiên bản."""

from datetime import UTC, datetime


async def lay_phien_ban(db) -> int:
    """Token phiên bản hiện tại, chưa có thì 0."""
    doc = await db["meta"].find_one({"_id": "dataset"})
    return int(doc.get("version", 0)) if doc else 0


async def cham_dataset(db) -> int:
    """Tăng phiên bản sau mỗi thêm/sửa/xóa POI, trả số mới."""
    doc = await db["meta"].find_one_and_update(
        {"_id": "dataset"},
        {"$inc": {"version": 1}, "$set": {"updated_at": datetime.now(UTC)}},
        upsert=True,
        return_document=True,
    )
    return int(doc["version"])


def etag_cho(version: int, lang: str) -> str:
    """Dấu vân tay dữ liệu theo phiên bản và ngôn ngữ."""
    return f'"{version}-{lang}"'


async def ghi_mo_xoa(db, poi_id, version: int) -> None:
    """Tombstone để delta báo máy khách xóa POI đã lưu."""
    await db["deleted_pois"].insert_one(
        {"poi_id": poi_id, "version": version, "at": datetime.now(UTC)}
    )
