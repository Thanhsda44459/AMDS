"""Seed dữ liệu cho test E2E (TEST-006/007/008/009).

Khác `seed_poi.py`: đây là dữ liệu **tối thiểu có kiểm soát** cho test tự động,
nó **xoá sạch** trước khi nạp để test luôn chạy trên trạng thái đã biết. Không
dùng script này cho môi trường thật.

Bao gồm:
- super admin `e2e-admin` để test luồng quản trị và duyệt chủ quán
- 5 POI ở Quận 4, có bản dịch `vi`/`en`/`zh` để test đổi ngôn ngữ
- `audio_status=ready` + `is_active=True` để POI hiện ngay, không phải chờ
  worker sinh audio (test E2E không nên phụ thuộc Edge-TTS có mạng)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from app.auth import bam_mat_khau
from app.config import settings
from app.permissions import dam_bao_roles, quyen_cua_role

ADMIN_E2E = "e2e-admin"
MAT_KHAU_E2E = "e2e123456"

# 5 quán thật ở Quận 4, tọa độ lấy xấp xỉ khu Vĩnh Khánh/Bến Thành.
POIS_E2E = [
    ("Bánh mì chảo Vĩnh Khánh", 10.7569, 106.7641),
    ("Ốc đêm Đào Vĩnh Khánh", 10.7590, 106.7650),
    ("Bún bò Gánh Cỏ Ởng", 10.7580, 106.7625),
    ("Cà phê sữa đá đường Lê Thánh Tôn", 10.7770, 106.7030),
    ("Cơm tấm Ba Ghiền", 10.7740, 106.7060),
]

# Bản dịch chỉ cần đủ để khác biệt ngôn ngữ thật sự xảy ra; nội dung ngắn là
# cố ý để POI card gọn và test không phụ thuộc câu chữ dài.
BAN_DICH = {
    "vi": ("Bánh mì chảo pate trứng ốp la.", "Món ăn sáng nổi tiếng Vĩnh Khánh."),
    "en": ("Paté bread roll with fried egg.", "A famous breakfast in Vinh Khanh."),
    "zh": ("法式面包配煎蛋。", "滨贤著名的早餐。"),
}


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongodb_db_name]

    for ten in ("pois", "poi_localizations", "admin_users", "owner_registrations",
                "owner_submissions", "owner_notifications", "audit_logs"):
        await db[ten].delete_many({})

    await dam_bao_roles(db)
    quyen = await quyen_cua_role(db, "super_admin")
    await db["admin_users"].insert_one(
        {"username": ADMIN_E2E, "password_hash": bam_mat_khau(MAT_KHAU_E2E),
         "role": "super_admin", "permissions": quyen}
    )

    for ten, (ten_quan, lat, lng) in enumerate(POIS_E2E):
        ket_qua = await db["pois"].insert_one(
            {
                "name": ten_quan,
                "description": BAN_DICH["vi"][0],
                "lat": lat,
                "lng": lng,
                "trigger_radius": 30,
                "audio_priority": ten,
                # Bật sẵn: test E2E không được phụ thuộc Edge-TTS có mạng,
                # và POI mới theo luồng thật sẽ chờ audio nên không hiện.
                "is_active": True,
                "audio_status": "ready",
                "activation_requested": False,
                "version": ten + 1,
            }
        )
        for lang, (mo_ta, ten_q) in BAN_DICH.items():
            await db["poi_localizations"].insert_one(
                {
                    "poi_id": ket_qua.inserted_id,
                    "lang": lang,
                    "name": ten_quan if lang == "vi" else ten_q,
                    "description": mo_ta,
                    "audio_url": None,
                }
            )

    print(f"[seed-e2e] {len(POIS_E2E)} POI, admin '{ADMIN_E2E}' / mật khẩu '{MAT_KHAU_E2E}'")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())