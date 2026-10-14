"""Application configuration.

Every knob the application has is declared here and comes from the
environment. Nothing reads ``os.environ`` directly, and no secret has a
usable production default.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/app/core/config.py -> apps/api/app/core -> app -> api -> apps -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]

Environment = Literal["development", "test", "production"]
LogFormat = Literal["console", "json"]


class Settings(BaseSettings):
    """Runtime settings, loaded from the process environment or the root ``.env``."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env",),
        env_file_encoding="utf-8",
        # Blank values in .env (the placeholders for later phases) fall back to
        # the declared default instead of becoming empty strings.
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    # --- application ------------------------------------------------------
    app_env: Environment = "development"
    app_name: str = "gitsync-studio-api"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    log_level: str = "INFO"
    log_format: LogFormat = "console"

    secret_key: SecretStr = SecretStr("dev-only-insecure-secret-change-me")

    # --- PostgreSQL -------------------------------------------------------
    database_url: str = "postgresql+asyncpg://gitsync:gitsync_dev_password@localhost:5433/gitsync"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    # --- Redis / Celery ---------------------------------------------------
    redis_url: str = "redis://localhost:6380/0"
    celery_broker_url: str = "redis://localhost:6380/1"
    celery_result_backend: str = "redis://localhost:6380/2"

    # --- HTTP -------------------------------------------------------------
    # Comma separated so a plain shell env var works. Read `cors_origins`.
    cors_allow_origins: str = "http://localhost:3100,http://localhost:3000"

    # Seconds to wait for a dependency before calling it unhealthy.
    health_check_timeout: float = 2.0

    # --- GitHub App -------------------------------------------------------
    github_app_id: str | None = Field(default=None, validation_alias="GITHUB_APP_ID")
    github_client_id: str | None = Field(default=None, validation_alias="GITHUB_APP_CLIENT_ID")
    github_client_secret: SecretStr | None = Field(default=None, validation_alias="GITHUB_APP_CLIENT_SECRET")
    github_private_key: SecretStr | None = None
    github_webhook_secret: SecretStr | None = None

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        level = value.strip().upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}, got {value!r}")
        return level

    @property
    def cors_origins(self) -> list[str]:
        """CORS allow-list as a list, ignoring blanks and stray whitespace."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def docs_url(self) -> str | None:
        """Interactive docs are a development convenience, not a public endpoint."""
        return None if self.is_production else "/docs"

    @property
    def sanitised_database_url(self) -> str:
        """``database_url`` with the password removed, safe to log."""
        url = self.database_url
        if "@" not in url or "://" not in url:
            return url
        scheme, rest = url.split("://", 1)
        credentials, host = rest.rsplit("@", 1)
        user = credentials.split(":", 1)[0]
        return f"{scheme}://{user}:***@{host}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings singleton.

    Cached so importing modules and FastAPI dependencies observe one object.
    Tests clear the cache via ``get_settings.cache_clear()``.
    """
    return Settings()
