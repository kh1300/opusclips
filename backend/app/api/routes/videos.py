from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.models.video import Video
from app.schemas.clip import ClipRead
from app.schemas.job import JobRead
from app.schemas.video import TranscriptRead, VideoCreated, VideoListItem, VideoLocalCreate, VideoRead, VideoUrlCreate
from app.services.storage import get_storage
from app.tasks.video_tasks import process_video_task
from app.utils.files import sanitize_filename

router = APIRouter(prefix="/videos", tags=["videos"])
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _download_url(request: Request, clip_id: UUID) -> str:
    return str(request.url_for("download_clip", clip_id=str(clip_id)))


def _serialize_clip(request: Request, clip) -> ClipRead:
    data = ClipRead.model_validate(clip)
    if clip.object_key:
        data.download_url = get_storage().url_for(clip.object_key) or _download_url(request, clip.id)
    return data


def _serialize_video(request: Request, video: Video) -> VideoRead:
    return VideoRead(
        id=video.id,
        source_type=video.source_type,
        source_url=video.source_url,
        filename=video.filename,
        duration_seconds=video.duration_seconds,
        status=video.status,
        error_message=video.error_message,
        created_at=video.created_at,
        updated_at=video.updated_at,
        clips=[_serialize_clip(request, clip) for clip in sorted(video.clips, key=lambda item: item.created_at)],
        jobs=[JobRead.model_validate(job) for job in sorted(video.jobs, key=lambda item: item.created_at, reverse=True)],
        transcript=TranscriptRead.model_validate(video.transcript) if video.transcript else None,
    )


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_read = 0
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            bytes_read += len(chunk)
            if bytes_read > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Upload exceeds {settings.max_upload_size_mb} MB",
                )
            output.write(chunk)


def _enqueue(job: Job, video: Video, db: Session) -> None:
    try:
        async_result = process_video_task.delay(str(job.id), str(video.id))
    except Exception as exc:
        job.status = "failed"
        job.error_message = "Could not enqueue processing job. Check Redis/Celery broker connectivity."
        video.status = "failed"
        video.error_message = "Could not enqueue processing job. Check Redis/Celery broker connectivity."
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue processing job. Check Redis/Celery broker connectivity.",
        ) from exc
    else:
        job.celery_task_id = async_result.id
        db.commit()


@router.post("/upload", response_model=VideoCreated, status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> VideoCreated:
    filename = sanitize_filename(file.filename)
    is_video_type = (file.content_type or "").startswith("video/")
    is_video_extension = Path(filename).suffix.lower() in VIDEO_EXTENSIONS
    if not (is_video_type or is_video_extension):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload must be a video file")

    video = Video(user_id=current_user.id, source_type="upload", filename=filename, status="uploaded")
    db.add(video)
    db.flush()

    temp_path = settings.work_dir / "uploads" / f"{video.id}-{filename}"
    try:
        await _save_upload(file, temp_path)

        object_key = f"users/{current_user.id}/videos/{video.id}/original/{filename}"
        get_storage().put_file(temp_path, object_key, file.content_type)
    finally:
        temp_path.unlink(missing_ok=True)

    video.original_object_key = object_key
    job = Job(video_id=video.id, user_id=current_user.id, status="uploaded", progress=0)
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    _enqueue(job, video, db)
    return VideoCreated(video_id=video.id, job_id=job.id, status=job.status)


@router.post("/from-url", response_model=VideoCreated, status_code=status.HTTP_202_ACCEPTED)
def create_video_from_url(
    payload: VideoUrlCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> VideoCreated:
    video = Video(
        user_id=current_user.id,
        source_type="url",
        source_url=str(payload.url),
        filename="source-video.mp4",
        status="uploaded",
    )
    db.add(video)
    db.flush()
    job = Job(video_id=video.id, user_id=current_user.id, status="uploaded", progress=0)
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    _enqueue(job, video, db)
    return VideoCreated(video_id=video.id, job_id=job.id, status=job.status)


@router.post("/from-local", response_model=VideoCreated, status_code=status.HTTP_202_ACCEPTED)
def create_video_from_local_file(
    payload: VideoLocalCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> VideoCreated:
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local sample files are only enabled when ENVIRONMENT=development",
        )

    sample_root = settings.local_sample_video_dir.resolve()
    requested_path = Path(payload.path).expanduser()
    resolved_path = (requested_path if requested_path.is_absolute() else sample_root / requested_path).resolve()

    if not _is_inside(resolved_path, sample_root):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Local sample path must be inside LOCAL_SAMPLE_VIDEO_DIR: {sample_root}",
        )
    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local sample video was not found: {resolved_path}",
        )
    if resolved_path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local sample must be a video file")

    video = Video(
        user_id=current_user.id,
        source_type="local",
        source_url=str(resolved_path),
        filename=sanitize_filename(resolved_path.name),
        status="uploaded",
    )
    db.add(video)
    db.flush()
    job = Job(video_id=video.id, user_id=current_user.id, status="uploaded", progress=0)
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    _enqueue(job, video, db)
    return VideoCreated(video_id=video.id, job_id=job.id, status=job.status)


@router.get("", response_model=list[VideoListItem])
def list_videos(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[VideoListItem]:
    videos = db.scalars(
        select(Video)
        .where(Video.user_id == current_user.id)
        .options(selectinload(Video.clips), selectinload(Video.jobs))
        .order_by(Video.created_at.desc())
    ).all()

    results: list[VideoListItem] = []
    for video in videos:
        latest_job = sorted(video.jobs, key=lambda item: item.created_at, reverse=True)[0] if video.jobs else None
        results.append(
            VideoListItem(
                id=video.id,
                source_type=video.source_type,
                source_url=video.source_url,
                filename=video.filename,
                status=video.status,
                error_message=video.error_message,
                clip_count=len(video.clips),
                latest_job=JobRead.model_validate(latest_job) if latest_job else None,
                created_at=video.created_at,
                updated_at=video.updated_at,
            )
        )
    return results


@router.get("/{video_id}", response_model=VideoRead)
def get_video(
    video_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> VideoRead:
    video = db.scalar(
        select(Video)
        .where(Video.id == video_id, Video.user_id == current_user.id)
        .options(
            selectinload(Video.clips),
            selectinload(Video.jobs),
            selectinload(Video.transcript),
        )
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return _serialize_video(request, video)
