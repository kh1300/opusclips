from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClipRead(BaseModel):
    id: UUID
    video_id: UUID
    title: str
    hook: str | None = None
    reason: str | None = None
    caption: str | None = None
    start_time: str
    end_time: str
    start_seconds: float
    end_seconds: float
    status: str
    download_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

