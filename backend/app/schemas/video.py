from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.schemas.clip import ClipRead
from app.schemas.job import JobRead


class VideoUrlCreate(BaseModel):
    url: HttpUrl


class VideoLocalCreate(BaseModel):
    path: str


class VideoCreated(BaseModel):
    video_id: UUID
    job_id: UUID
    status: str


class TranscriptRead(BaseModel):
    text: str
    language: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VideoRead(BaseModel):
    id: UUID
    source_type: str
    source_url: str | None = None
    filename: str | None = None
    duration_seconds: float | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    clips: list[ClipRead] = []
    jobs: list[JobRead] = []
    transcript: TranscriptRead | None = None

    model_config = ConfigDict(from_attributes=True)


class VideoListItem(BaseModel):
    id: UUID
    source_type: str
    source_url: str | None = None
    filename: str | None = None
    status: str
    error_message: str | None = None
    clip_count: int = 0
    latest_job: JobRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
