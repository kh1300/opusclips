from pathlib import Path

from app.utils.timecode import seconds_to_srt_timestamp


def _ass_timestamp(seconds: float) -> str:
    seconds = max(0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole_seconds = int(seconds % 60)
    centiseconds = int(round((seconds - int(seconds)) * 100))
    if centiseconds == 100:
        whole_seconds += 1
        centiseconds = 0
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def _clean_caption(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def _caption_entries(
    segments: list[dict],
    clip_start: float,
    clip_end: float,
    fallback_caption: str | None = None,
) -> list[tuple[float, float, str]]:
    entries: list[tuple[float, float, str]] = []
    for segment in segments:
        try:
            segment_start = float(segment["start"])
            segment_end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue

        if segment_end <= clip_start or segment_start >= clip_end:
            continue

        local_start = max(segment_start, clip_start) - clip_start
        local_end = min(segment_end, clip_end) - clip_start
        if local_end - local_start < 0.25:
            continue

        text = _clean_caption(str(segment.get("text", "")))
        if not text:
            continue

        entries.append((local_start, local_end, text))

    if not entries and fallback_caption:
        entries.append((0, clip_end - clip_start, _clean_caption(fallback_caption)))

    return entries


def write_clip_srt(
    segments: list[dict],
    clip_start: float,
    clip_end: float,
    output_path: Path,
    fallback_caption: str | None = None,
) -> Path:
    entries = []
    for index, (start, end, text) in enumerate(
        _caption_entries(segments, clip_start, clip_end, fallback_caption),
        start=1,
    ):
        entries.append(
            "\n".join(
                [
                    str(index),
                    f"{seconds_to_srt_timestamp(start)} --> {seconds_to_srt_timestamp(end)}",
                    text,
                    "",
                ]
            )
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(entries), encoding="utf-8")
    return output_path


def _escape_ass_text(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def write_clip_ass(
    segments: list[dict],
    clip_start: float,
    clip_end: float,
    output_path: Path,
    fallback_caption: str | None = None,
) -> Path:
    events = []
    animation = r"{\fad(90,90)\t(0,130,\fscx108\fscy108)\t(130,240,\fscx100\fscy100)}"
    for start, end, text in _caption_entries(segments, clip_start, clip_end, fallback_caption):
        events.append(
            "Dialogue: 0,"
            f"{_ass_timestamp(start)},{_ass_timestamp(end)},Default,,0,0,0,,"
            f"{animation}{_escape_ass_text(text)}"
        )

    ass_text = "\n".join(
        [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,76,&H00FFFFFF,&H000000FF,&H85000000,&H85000000,-1,0,0,0,100,100,0,0,3,4,0,2,92,92,150,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
            *events,
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ass_text, encoding="utf-8")
    return output_path
