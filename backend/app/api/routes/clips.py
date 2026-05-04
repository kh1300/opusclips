from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.clip import Clip
from app.models.user import User
from app.services.storage import get_storage
from app.utils.files import sanitize_filename

router = APIRouter(prefix="/clips", tags=["clips"])


@router.get("/{clip_id}/download", name="download_clip")
def download_clip(
    clip_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    clip = db.scalar(select(Clip).where(Clip.id == clip_id, Clip.user_id == current_user.id))
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    if clip.status != "completed" or not clip.object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Clip is not ready")

    storage = get_storage()
    local_path = storage.local_path_for(clip.object_key)
    filename = sanitize_filename(f"{clip.title}.mp4")
    if local_path and local_path.exists():
        return FileResponse(local_path, media_type="video/mp4", filename=filename)

    url = storage.url_for(clip.object_key)
    if not url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Clip file is unavailable")
    return RedirectResponse(url=url)

