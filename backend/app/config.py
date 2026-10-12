"""Cấu hình ứng dụng đọc từ biến môi trường và tệp .env.

Mọi thông số thay theo môi trường (dev, staging, production) nằm ở đây,
code nghiệp vụ chỉ đọc qua `settings`, không gọi `os.getenv` rải rác.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Thông số Phase 0-4: MongoDB, môi trường, bí mật JWT, seed admin."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "amds"
    # Môi trường chạy: dev thì nới lỏng (cookie không Secure, secret mặc định).
    app_env: str = "dev"
    jwt_secret: str = "dev-access-secret-doi-khi-deploy"
    refresh_secret: str = "dev-refresh-secret-doi-khi-deploy"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    redis_url: str = "redis://localhost:6379"
    # Fernet mã hóa PII, AI provider: mock cho dev, proxypal/gemini khi có key.
    pii_key: str = ""
    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_api_url: str = ""
    # Phase 10: origin được phép gửi analytics và quan sát runtime.
    # Rỗng nghĩa là chỉ chấp nhận request không kèm Origin (curl, test).
    analytics_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()


def la_dev() -> bool:
    """Chạy local thì nới lỏng Secure cookie và secret mặc định."""
    return settings.app_env == "dev"


def kiem_tra_bi_mat() -> None:
    """Fail-fast: ngoài dev mà thiếu secret thì từ chối khởi động."""
    if la_dev():
        return
    thieu = [
        ten
        for ten, gia_tri in (
            ("JWT_SECRET", settings.jwt_secret),
            ("REFRESH_TOKEN_SECRET", settings.refresh_secret),
        )
        if gia_tri == ""
    ]
    if thieu:
        raise RuntimeError(f"Thiếu biến môi trường bắt buộc: {', '.join(thieu)}")
