import re
from pathlib import Path


SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str | None, fallback: str = "video.mp4") -> str:
    cleaned = SAFE_FILENAME_RE.sub("-", filename or fallback).strip(".-")
    return cleaned or fallback


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

