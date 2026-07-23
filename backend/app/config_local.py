"""Local development configuration using SQLite."""

from functools import lru_cache
from pydantic_settings import BaseSettings
import os

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LocalSettings(BaseSettings):
    """Settings for local development without Docker."""

    app_name: str = "AI Work Studio"
    app_env: str = "local"
    app_debug: bool = True

    # JWT
    jwt_secret_key: str = "dev-secret-key-do-not-use-in-production-abc123xyz"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    @property
    def database_url(self) -> str:
        db_path = os.path.join(_backend_dir, "dev.db")
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def database_url_sync(self) -> str:
        db_path = os.path.join(_backend_dir, "dev.db")
        return f"sqlite:///{db_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_local_settings() -> LocalSettings:
    return LocalSettings()
