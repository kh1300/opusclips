from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClipForge API"
    environment: Literal["development", "staging", "production"] = "development"
    api_v1_prefix: str = "/api"
    frontend_url: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/clipforge"
    )
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    auto_create_tables: bool = True

    require_auth: bool = False
    supabase_url: AnyHttpUrl | None = None
    supabase_jwt_secret: str | None = None

    openai_api_key: str | None = None
    openai_whisper_model: str = "whisper-1"
    openai_clip_model: str = "gpt-4o-mini"
    mock_ai: bool = False

    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: Path = Path("/app/storage")
    s3_bucket: str | None = None
    s3_region: str = "auto"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_public_base_url: str | None = None
    presigned_url_ttl_seconds: int = 3600

    max_upload_size_mb: int = 2048
    work_dir: Path = Path("/app/work")
    local_sample_video_dir: Path = Path("/app/samples")
    clips_per_video_min: int = 5
    clips_per_video_max: int = 10
    clip_min_seconds: int = 20
    clip_max_seconds: int = 60
    ffmpeg_threads: int = 2
    yt_dlp_format: str = "bv*+ba/b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "celery_broker_url",
        "celery_result_backend",
        "supabase_url",
        "supabase_jwt_secret",
        "openai_api_key",
        "s3_bucket",
        "s3_endpoint_url",
        "s3_access_key_id",
        "s3_secret_access_key",
        "s3_public_base_url",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.environment == "production" and self.mock_ai:
            raise ValueError("MOCK_AI=true is forbidden when ENVIRONMENT=production")
        return self

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.local_storage_path.mkdir(parents=True, exist_ok=True)
    settings.work_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
