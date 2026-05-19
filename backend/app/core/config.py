"""Application settings for the Conforma-AI backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="conforma-ai", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS"),
    )
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_pro_model: str = Field(
        default="gemini-3.1-pro-preview",
        alias="GEMINI_PRO_MODEL",
    )
    gemini_flash_model: str = Field(
        default="gemini-3-flash-preview",
        alias="GEMINI_FLASH_MODEL",
    )
    gemini_timeout_seconds: float = Field(
        default=30.0,
        alias="GEMINI_TIMEOUT_SECONDS",
    )
    database_url: str = Field(
        default="postgresql://conforma:conforma_dev_password@localhost:5432/conforma_ai",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="local-dev-secret", alias="SECRET_KEY")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized CORS origins from the comma-separated env value."""

        items = [origin.strip() for origin in self.allowed_origins.split(",")]
        return [origin for origin in items if origin]

    @property
    def cors_origin_regex(self) -> str | None:
        """Return a regex for wildcard origins such as Vercel preview URLs."""

        wildcard_origins = [origin for origin in self.cors_origins if "*" in origin]
        if not wildcard_origins:
            return None

        patterns = [
            "^" + re.escape(origin).replace("\\*", "[^/]+") + "$"
            for origin in wildcard_origins
        ]
        return "|".join(patterns)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build and cache the application settings object."""

    return Settings()


settings = get_settings()
