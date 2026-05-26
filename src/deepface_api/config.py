"""Runtime configuration powered by pydantic-settings.

Settings are read from environment variables (prefix ``DEEPFACE_``) and
optionally from a ``.env`` file located next to the working directory.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All values can be overridden by environment variables prefixed with
    ``DEEPFACE_`` (e.g. ``DEEPFACE_SERVER_PORT=9000``). Legacy unprefixed
    variables (``SERVER_PORT`` etc.) are still honored for backwards
    compatibility.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DEEPFACE_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "deepface-api"
    app_description: str = (
        "Face detection and facial attribute analysis API powered by RetinaFace + DeepFace."
    )

    server_host: str = Field(default="0.0.0.0", description="Bind host")
    server_port: int = Field(default=8008, ge=1, le=65535)

    output_dir: Path = Field(default=Path("./output"))
    max_upload_size_mb: int = Field(default=10, ge=1, le=512)

    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins (comma-separated env value supported).",
    )
    cors_allow_credentials: bool = False

    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=False, description="Emit logs as JSON lines")

    enable_docs: bool = Field(default=True, description="Expose /docs and /redoc")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("output_dir")
    @classmethod
    def _ensure_output_dir(cls, value: Path) -> Path:
        value.mkdir(parents=True, exist_ok=True)
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide Settings, honoring legacy unprefixed env vars."""

    import os

    legacy_aliases = {
        "SERVER_PORT": "DEEPFACE_SERVER_PORT",
        "SERVER_HOST": "DEEPFACE_SERVER_HOST",
        "OUTPUT_DIR": "DEEPFACE_OUTPUT_DIR",
        "MAX_UPLOAD_SIZE_MB": "DEEPFACE_MAX_UPLOAD_SIZE_MB",
        "LOG_LEVEL": "DEEPFACE_LOG_LEVEL",
    }
    for legacy, modern in legacy_aliases.items():
        if legacy in os.environ and modern not in os.environ:
            os.environ[modern] = os.environ[legacy]

    return Settings()
