from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SSluntan"
    environment: str = "development"
    debug: bool = True

    # 前后端分离：API 统一前缀，前端通过 CORS 或 Vite proxy 访问。
    api_prefix: str = "/api"
    enable_legacy_web_ui: bool = False

    secret_key: str = "dev-only-change-me-please-use-a-32-byte-secret"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite+aiosqlite:///./forum.db"
    auto_create_tables: bool = True
    seed_default_data: bool = True

    cookie_secure: bool = False
    session_cookie_name: str = "forum_session"
    csrf_cookie_name: str = "forum_csrf"

    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
