"""Mô hình POI v2, thêm bán kính geofence và ưu tiên audio.

V1 chỉ có 5 trường. V2 thêm `trigger_radius` và `audio_priority`
có giá trị mặc định nên dữ liệu cũ vẫn đọc được (tương thích ngược).
"""

from pydantic import BaseModel, Field


class Poi(BaseModel):
    """Một quán ăn trên bản đồ ở V2."""

    id: str | None = Field(default=None)
    name: str = Field(min_length=1)
    description: str = Field(default="")
    lat: float
    lng: float
    # Bán kính vòng geofence (m), validate chặt ở POI-010.
    trigger_radius: float = Field(default=30)
    # Ưu tiên đọc khi nhiều quán cùng đủ điều kiện, số nhỏ đọc trước.
    audio_priority: int = Field(default=0)
