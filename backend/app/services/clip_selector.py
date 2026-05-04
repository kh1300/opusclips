from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.utils.timecode import parse_timecode, seconds_to_timecode


@dataclass
class ClipCandidate:
    title: str
    start_time: str
    end_time: str
    hook: str
    reason: str
    caption: str
    start_seconds: float
    end_seconds: float


def _segment_lines(segments: list[dict]) -> list[str]:
    lines: list[str] = []
    for segment in segments:
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        text = " ".join(str(segment.get("text", "")).split())
        if text:
            lines.append(f"[{seconds_to_timecode(start)} - {seconds_to_timecode(end)}] {text}")
    return lines


def _chunk_lines(lines: list[str], max_chars: int = 42000) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        if current and size + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current = []
            size = 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def _json_from_text(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", cleaned)
        if not match:
            raise
        return json.loads(match.group(1))


def _call_gpt(prompt: str) -> Any:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for GPT clip selection. "
            "Set OPENAI_API_KEY or, for local development only, set MOCK_AI=true."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        completion = client.chat.completions.create(
            model=settings.openai_clip_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert short-form video editor. Choose only clips that can stand alone, "
                        "have clear hooks, and are valid within the supplied timecodes. Return JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise RuntimeError(
            "OpenAI GPT clip selection failed. Check OPENAI_API_KEY, billing, network access, "
            f"and the configured model '{settings.openai_clip_model}'. Provider error: {exc}"
        ) from exc
    content = completion.choices[0].message.content or "[]"
    return _json_from_text(content)


def _coerce_candidates(payload: Any, video_duration: float | None) -> list[ClipCandidate]:
    items = payload.get("clips", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []

    candidates: list[ClipCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            start_seconds = parse_timecode(str(item["start_time"]))
            end_seconds = parse_timecode(str(item["end_time"]))
        except (KeyError, TypeError, ValueError):
            continue

        duration = end_seconds - start_seconds
        if duration < settings.clip_min_seconds or duration > settings.clip_max_seconds:
            continue
        if start_seconds < 0 or (video_duration is not None and end_seconds > video_duration + 1):
            continue

        title = str(item.get("title") or "Untitled clip").strip()[:255]
        candidates.append(
            ClipCandidate(
                title=title,
                start_time=seconds_to_timecode(start_seconds),
                end_time=seconds_to_timecode(end_seconds),
                hook=str(item.get("hook") or "").strip(),
                reason=str(item.get("reason") or "").strip(),
                caption=str(item.get("caption") or "").strip(),
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
        )
    return candidates


def _mock_select_viral_clips(video_duration: float | None) -> list[ClipCandidate]:
    duration = float(video_duration or 0)
    if duration < settings.clip_min_seconds:
        raise RuntimeError(
            f"Video is {duration:.1f}s long, but clips must be at least {settings.clip_min_seconds}s. "
            "Use a longer sample video or lower CLIP_MIN_SECONDS for development."
        )

    clip_length = min(float(settings.clip_max_seconds), max(float(settings.clip_min_seconds), min(38.0, duration)))
    available_span = max(0.0, duration - clip_length)
    target_count = min(settings.clips_per_video_max, max(settings.clips_per_video_min, int(duration // clip_length)))
    target_count = max(1, min(target_count, settings.clips_per_video_max))
    step = available_span / target_count if target_count else 0

    candidates: list[ClipCandidate] = []
    for index in range(target_count):
        start = min(available_span, round(index * step + (3 if index else 0), 2))
        end = min(duration, start + clip_length)
        if end - start < settings.clip_min_seconds:
            start = max(0.0, end - settings.clip_min_seconds)
        candidates.append(
            ClipCandidate(
                title=f"Sample highlight {index + 1}",
                start_time=seconds_to_timecode(start),
                end_time=seconds_to_timecode(end),
                hook="A high-signal moment from the local development transcript.",
                reason="MOCK_AI=true generated this deterministic clip candidate so the full render path can be tested locally.",
                caption="This is a local development caption generated by mock AI.",
                start_seconds=start,
                end_seconds=end,
            )
        )
    return candidates


def select_viral_clips(text: str, segments: list[dict], video_duration: float | None) -> list[ClipCandidate]:
    if settings.mock_ai:
        return _mock_select_viral_clips(video_duration)

    lines = _segment_lines(segments)
    if not lines and text:
        lines = [text]

    all_candidates: list[ClipCandidate] = []
    for chunk_number, chunk in enumerate(_chunk_lines(lines), start=1):
        prompt = f"""
Analyze this transcript chunk and choose the best viral short-form clips.
Return JSON only:
[
  {{
    "title": "...",
    "start_time": "00:01:20",
    "end_time": "00:02:05",
    "hook": "...",
    "reason": "...",
    "caption": "..."
  }}
]

Rules:
- Each clip should be {settings.clip_min_seconds}-{settings.clip_max_seconds} seconds
- Choose high-energy moments
- Prefer emotional, surprising, useful, controversial, or funny parts
- Avoid boring introductions
- Ensure start and end times are valid
- Return at most 5 clips for this chunk

Transcript chunk {chunk_number}:
{chunk}
""".strip()
        payload = _call_gpt(prompt)
        all_candidates.extend(_coerce_candidates(payload, video_duration))

    unique: dict[tuple[int, int], ClipCandidate] = {}
    for candidate in all_candidates:
        key = (round(candidate.start_seconds), round(candidate.end_seconds))
        unique.setdefault(key, candidate)

    candidates = list(unique.values())
    if len(candidates) <= settings.clips_per_video_max:
        return candidates[: settings.clips_per_video_max]

    rerank_prompt = f"""
Choose the best {settings.clips_per_video_max} clips from these candidates.
Return JSON only as an array in the same schema. Prefer the strongest hooks and remove repetitive picks.

Candidates:
{json.dumps([candidate.__dict__ for candidate in candidates], indent=2)}
""".strip()
    reranked_payload = _call_gpt(rerank_prompt)
    reranked = _coerce_candidates(reranked_payload, video_duration)
    return reranked[: settings.clips_per_video_max] or candidates[: settings.clips_per_video_max]
