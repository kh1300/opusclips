# ClipForge

Production-ready MVP for an OpusClip-style workflow: upload or link a long video, transcribe it, ask GPT for the strongest short-form moments, render 9:16 clips with burned subtitles, and show downloadable clips in a dashboard.

## Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Celery
- Database: PostgreSQL, compatible with Supabase Postgres
- Queue: Redis + Celery
- Storage: local dev storage or Cloudflare R2/AWS S3 through the S3 API
- Video tooling: FFmpeg, ffprobe, yt-dlp
- AI: OpenAI Whisper transcription and OpenAI GPT clip selection
- Auth: Supabase Auth bearer tokens, optional in local development

## Local Setup

1. Copy environment values:

   ```bash
   cp .env.example .env
   ```

2. Add `OPENAI_API_KEY` to `.env`, unless you are running the development sample mode with `MOCK_AI=true`.

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Open:

   - Frontend: http://localhost:3000
   - Backend docs: http://localhost:8000/docs

## Development Sample Mode

Put a video file in `samples/` and submit its filename from the dashboard local sample field. The backend accepts local files only when `ENVIRONMENT=development`, and only from `LOCAL_SAMPLE_VIDEO_DIR`.

Set `MOCK_AI=true` for a no-OpenAI smoke test. Mock AI generates deterministic transcript segments and clip candidates, then still runs real FFmpeg audio extraction, vertical clipping, subtitle generation, burned captions, storage, database writes, dashboard status updates, previews, and downloads.

`MOCK_AI=true` is refused when `ENVIRONMENT=production`.

## Pipeline

`POST /api/videos/upload` stores the uploaded file and queues a Celery job.
`POST /api/videos/from-url` queues a job that downloads the source with `yt-dlp`.
`POST /api/videos/from-local` queues a development-only job from a video already inside `LOCAL_SAMPLE_VIDEO_DIR`.

The worker then stores or retrieves the video, extracts audio, transcribes it, asks GPT for viral clips, validates clip times, generates subtitles, renders 1080x1920 clips with burned animated captions, stores the files, and writes metadata to Postgres.
