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

## Project Structure

```text
backend/
  app/
    api/routes/        FastAPI routes
    core/              settings
    models/            users, videos, clips, transcripts, jobs
    services/          storage, OpenAI, subtitles, FFmpeg, pipeline
    tasks/             Celery app and video task
  migrations/          initial SQL schema for managed Postgres setup
frontend/
  app/                 Next.js app router
  components/          landing and dashboard UI
  lib/                 API and Supabase clients
infra/postgres/        local Postgres init
docker-compose.yml
```

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

The local Compose setup uses local object storage in a Docker volume. To use Cloudflare R2 or AWS S3, set `STORAGE_BACKEND=s3` plus the `S3_*` values in `.env`.

## Development Sample Mode

For a no-upload local test, put a video file in `samples/` and submit its filename from the dashboard local sample field. The backend accepts local files only when `ENVIRONMENT=development`, and only from `LOCAL_SAMPLE_VIDEO_DIR`.

For a no-OpenAI smoke test, set:

```bash
MOCK_AI=true
```

With `MOCK_AI=true`, the worker generates deterministic mock transcript segments and mock clip candidates, then still runs the real FFmpeg audio extraction, vertical clipping, subtitle generation, burned captions, storage, database writes, dashboard status updates, previews, and downloads.

`MOCK_AI=true` is refused when `ENVIRONMENT=production`; the app fails at startup with a clear configuration error. With `MOCK_AI=false`, missing OpenAI credentials fail the job clearly in the dashboard.

## Supabase Auth

Local development defaults to `REQUIRE_AUTH=false`, which creates a dev user automatically. For Supabase Auth:

1. Set `REQUIRE_AUTH=true`.
2. Set `SUPABASE_JWT_SECRET` for backend JWT verification.
3. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` for the frontend.

The frontend sends Supabase access tokens to the backend. The backend stores the Supabase subject in the `users.supabase_id` column.

## Pipeline

`POST /api/videos/upload` stores the uploaded file and queues a Celery job.
`POST /api/videos/from-url` queues a job that downloads the source with `yt-dlp`.
`POST /api/videos/from-local` queues a development-only job from a video already inside `LOCAL_SAMPLE_VIDEO_DIR`.

The worker then:

1. Stores or retrieves the original video.
2. Extracts audio with FFmpeg.
3. Transcribes audio with OpenAI Whisper.
4. Sends timestamped transcript chunks to GPT for viral clip selection.
5. Validates 20-60 second candidate clips.
6. Generates `.srt` subtitles from Whisper segments.
7. Builds an animated ASS subtitle render file, then cuts vertical 1080x1920 clips with FFmpeg and burns the captions into the video.
8. Stores final clips and metadata in Postgres.

Job/video statuses are `uploaded`, `transcribing`, `analyzing`, `clipping`, `subtitling`, `completed`, and `failed`.

## API Routes

- `POST /api/videos/upload`
- `POST /api/videos/from-url`
- `POST /api/videos/from-local`
- `GET /api/videos`
- `GET /api/videos/{id}`
- `GET /api/jobs/{id}`
- `GET /api/clips/{id}/download`

## Production Notes

- Use `STORAGE_BACKEND=s3` with R2/S3 credentials instead of local storage.
- Set `REQUIRE_AUTH=true` and configure Supabase JWT values.
- Replace `AUTO_CREATE_TABLES=true` with managed migrations before scaling teams.
- Run Celery workers separately from the API and tune worker concurrency based on CPU capacity.
- FFmpeg rendering is CPU-intensive; use a worker queue with enough disk space in `WORK_DIR`.
- Stripe is intentionally left for the next milestone; no payment gates are stubbed in this MVP.
