from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.clip import Clip
from app.models.job import Job
from app.models.transcript import Transcript
from app.models.video import Video
from app.services.clip_selector import ClipCandidate, select_viral_clips
from app.services.storage import get_storage
from app.services.subtitles import write_clip_ass, write_clip_srt
from app.services.transcription import transcribe_audio
from app.services.video_tools import burn_vertical_clip, download_video, extract_audio, probe_duration
from app.utils.files import sanitize_filename


def _set_status(db: Session, video: Video, job: Job, status: str, progress: float) -> None:
    video.status = status
    job.status = status
    job.progress = progress
    db.commit()


def _mark_failed(db: Session, video: Video | None, job: Job | None, message: str) -> None:
    if video:
        video.status = "failed"
        video.error_message = message
    if job:
        job.status = "failed"
        job.error_message = message
        job.progress = 100
    if video:
        db.execute(
            update(Clip)
            .where(Clip.video_id == video.id, Clip.status != "completed")
            .values(status="failed")
        )
    db.commit()


def _clip_to_model(candidate: ClipCandidate, video: Video) -> Clip:
    return Clip(
        video_id=video.id,
        user_id=video.user_id,
        title=candidate.title,
        hook=candidate.hook,
        reason=candidate.reason,
        caption=candidate.caption,
        start_time=candidate.start_time,
        end_time=candidate.end_time,
        start_seconds=candidate.start_seconds,
        end_seconds=candidate.end_seconds,
        status="clipping",
    )


def process_video_job(job_id: str, video_id: str) -> None:
    storage = get_storage()
    db = SessionLocal()
    video: Video | None = None
    job: Job | None = None
    work_dir = settings.work_dir / str(job_id)

    try:
        video = db.get(Video, uuid.UUID(video_id))
        job = db.get(Job, uuid.UUID(job_id))
        if not video or not job:
            raise RuntimeError("Video or job not found")

        work_dir.mkdir(parents=True, exist_ok=True)
        source_path = work_dir / "original.mp4"

        if video.source_type == "url":
            _set_status(db, video, job, "uploaded", 5)
            downloaded_path = download_video(str(video.source_url), source_path)
            original_key = f"users/{video.user_id}/videos/{video.id}/original.mp4"
            storage.put_file(downloaded_path, original_key, "video/mp4")
            video.original_object_key = original_key
            video.filename = sanitize_filename(video.filename or "source-video.mp4")
            db.commit()
        elif video.source_type == "local":
            if settings.environment != "development":
                raise RuntimeError("Local sample video processing is only available when ENVIRONMENT=development")
            if not video.source_url:
                raise RuntimeError("Local sample video path is missing")
            sample_root = settings.local_sample_video_dir.resolve()
            local_source = Path(video.source_url).resolve()
            try:
                local_source.relative_to(sample_root)
            except ValueError as exc:
                raise RuntimeError(f"Local sample video must be inside LOCAL_SAMPLE_VIDEO_DIR: {sample_root}") from exc
            if not local_source.exists():
                raise RuntimeError(f"Local sample video does not exist: {local_source}")
            shutil.copyfile(local_source, source_path)
            original_key = f"users/{video.user_id}/videos/{video.id}/original/{sanitize_filename(local_source.name)}"
            storage.put_file(source_path, original_key, "video/mp4")
            video.original_object_key = original_key
            video.filename = sanitize_filename(video.filename or local_source.name)
            db.commit()
        elif video.original_object_key:
            storage.download_file(video.original_object_key, source_path)
        else:
            raise RuntimeError("Uploaded video is missing from storage")

        video.duration_seconds = probe_duration(source_path)
        db.commit()

        _set_status(db, video, job, "transcribing", 20)
        audio_path = extract_audio(source_path, work_dir / "audio.mp3")
        transcript_data = transcribe_audio(audio_path, duration_seconds=video.duration_seconds)
        if not transcript_data["text"]:
            raise RuntimeError("Transcription returned no text")

        transcript = video.transcript or Transcript(video_id=video.id, text="")
        transcript.text = transcript_data["text"]
        transcript.segments_json = transcript_data["segments"]
        transcript.language = transcript_data["language"]
        db.add(transcript)
        db.commit()

        _set_status(db, video, job, "analyzing", 45)
        candidates = select_viral_clips(
            transcript.text,
            transcript.segments_json,
            video.duration_seconds,
        )
        if not candidates:
            raise RuntimeError("No valid clips were selected from the transcript")

        db.execute(delete(Clip).where(Clip.video_id == video.id))
        clips = [_clip_to_model(candidate, video) for candidate in candidates]
        db.add_all(clips)
        db.commit()
        for clip in clips:
            db.refresh(clip)

        _set_status(db, video, job, "clipping", 60)
        total = len(clips)
        for index, clip in enumerate(clips, start=1):
            clip.status = "subtitling"
            job.status = "subtitling"
            job.progress = 60 + ((index - 1) / total) * 35
            video.status = "subtitling"
            db.commit()

            srt_path = work_dir / "subtitles" / f"{clip.id}.srt"
            ass_path = work_dir / "subtitles" / f"{clip.id}.ass"
            write_clip_srt(
                transcript.segments_json,
                clip.start_seconds,
                clip.end_seconds,
                srt_path,
                fallback_caption=clip.caption,
            )
            write_clip_ass(
                transcript.segments_json,
                clip.start_seconds,
                clip.end_seconds,
                ass_path,
                fallback_caption=clip.caption,
            )
            srt_key = f"users/{video.user_id}/videos/{video.id}/subtitles/{clip.id}.srt"
            storage.put_file(srt_path, srt_key, "application/x-subrip")

            output_path = work_dir / "clips" / f"{clip.id}.mp4"
            burn_vertical_clip(
                source_path,
                output_path,
                ass_path,
                clip.start_seconds,
                clip.end_seconds,
            )
            clip_key = f"users/{video.user_id}/videos/{video.id}/clips/{clip.id}.mp4"
            storage.put_file(output_path, clip_key, "video/mp4")

            clip.object_key = clip_key
            clip.srt_object_key = srt_key
            clip.status = "completed"
            job.progress = 60 + (index / total) * 35
            db.commit()

        _set_status(db, video, job, "completed", 100)
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception as exc:
        _mark_failed(db, video, job, str(exc))
        raise
    finally:
        db.close()
