"""Cấu hình ứng dụng đọc từ biến môi trường và tệp .env.

Mọi thông số thay theo môi trường (dev, staging, production) nằm ở đây,
code nghiệp vụ chỉ đọc qua `settings`, không gọi `os.getenv` rải rác.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Thông số Phase 0, chỉ gồm MongoDB, chưa gồm bí mật JWT."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "amds"


settings = Settings()
