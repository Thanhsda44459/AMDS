"""Mô hình POI v1, cố tình tối giản để hiện danh sách.

V1 gộp tiếng Việt thẳng trong POI, chưa có ảnh, bán kính,
đa ngôn ngữ. Sẽ đổi ở POI-006, LOC-001, POI-011.
"""

from pydantic import BaseModel, Field


class Poi(BaseModel):
    """Một quán ăn trên bản đồ ở V1."""

    id: str | None = Field(default=None)
    name: str = Field(min_length=1)
    description: str = Field(default="")
    lat: float
    lng: float
