from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.core.config import settings


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        tool = command[0]
        raise RuntimeError(
            f"Required video tool '{tool}' is not installed or is not on PATH. "
            f"Install '{tool}' in the API/worker environment and retry the job."
        ) from exc
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Command failed").strip()
        raise RuntimeError(f"{command[0]} failed: {message[-3900:]}")
    return result.stdout


def download_video(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "yt-dlp",
            "-f",
            settings.yt_dlp_format,
            "--merge-output-format",
            "mp4",
            "-o",
            str(output_path),
            url,
        ]
    )
    return output_path


def probe_duration(video_path: Path) -> float | None:
    output = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video_path),
        ]
    )
    data = json.loads(output)
    duration = data.get("format", {}).get("duration")
    return float(duration) if duration is not None else None


def extract_audio(video_path: Path, audio_path: Path) -> Path:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "mp3",
            str(audio_path),
        ]
    )
    return audio_path


def _escape_filter_path(path: Path) -> str:
    escaped = path.resolve().as_posix().replace("\\", "/")
    escaped = escaped.replace(":", r"\:").replace("'", r"\'")
    return escaped


def burn_vertical_clip(
    source_path: Path,
    output_path: Path,
    subtitle_path: Path,
    start_seconds: float,
    end_seconds: float,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, end_seconds - start_seconds)
    if subtitle_path.suffix.lower() == ".ass":
        subtitle_filter = f"ass='{_escape_filter_path(subtitle_path)}'"
    else:
        subtitle_filter = (
            f"subtitles='{_escape_filter_path(subtitle_path)}':"
            "force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H90000000,BackColour=&H90000000,BorderStyle=3,"
            "Outline=2,Shadow=0,Alignment=2,MarginV=140'"
        )
    filters = ",".join(
        [
            "scale=1080:1920:force_original_aspect_ratio=increase",
            "crop=1080:1920",
            subtitle_filter,
        ]
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_seconds:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            filters,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-threads",
            str(settings.ffmpeg_threads),
            str(output_path),
        ]
    )
    return output_path
