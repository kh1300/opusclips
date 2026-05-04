from pathlib import Path

from openai import OpenAI

from app.core.config import settings


MOCK_LINES = [
    "Here is the part that usually makes people stop scrolling because the stakes become clear.",
    "The surprising lesson is that a small change in the workflow creates a much better result.",
    "This moment has a clean hook, a practical takeaway, and enough tension to work as a short clip.",
    "The speaker lands the point with a useful example that can stand on its own.",
    "This section is paced like a short-form highlight and leads naturally into the next beat.",
]


def _mock_transcription(duration_seconds: float | None) -> dict:
    duration = max(float(duration_seconds or 90), float(settings.clip_min_seconds))
    segment_length = 6.0
    segments = []
    cursor = 0.0
    index = 0

    while cursor < duration:
        end = min(duration, cursor + segment_length)
        text = MOCK_LINES[index % len(MOCK_LINES)]
        segments.append(
            {
                "id": index,
                "start": round(cursor, 2),
                "end": round(end, 2),
                "text": text,
            }
        )
        cursor = end
        index += 1

    return {
        "text": " ".join(segment["text"] for segment in segments),
        "segments": segments,
        "language": "mock",
    }


def transcribe_audio(audio_path: Path, duration_seconds: float | None = None) -> dict:
    if settings.mock_ai:
        return _mock_transcription(duration_seconds)

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for Whisper transcription. "
            "Set OPENAI_API_KEY or, for local development only, set MOCK_AI=true."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        with audio_path.open("rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
    except Exception as exc:
        raise RuntimeError(
            "OpenAI Whisper transcription failed. Check OPENAI_API_KEY, billing, network access, "
            f"and the configured model '{settings.openai_whisper_model}'. Provider error: {exc}"
        ) from exc

    data = transcript.model_dump() if hasattr(transcript, "model_dump") else dict(transcript)
    return {
        "text": data.get("text", ""),
        "segments": data.get("segments") or [],
        "language": data.get("language"),
    }
