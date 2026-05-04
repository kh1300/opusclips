CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  supabase_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(320),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_type VARCHAR(32) NOT NULL,
  source_url TEXT,
  filename VARCHAR(512),
  original_object_key VARCHAR(1024),
  duration_seconds DOUBLE PRECISION,
  status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  celery_task_id VARCHAR(255),
  status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
  progress DOUBLE PRECISION NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transcripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID UNIQUE NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  segments_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  language TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  hook TEXT,
  reason TEXT,
  caption TEXT,
  start_time VARCHAR(16) NOT NULL,
  end_time VARCHAR(16) NOT NULL,
  start_seconds DOUBLE PRECISION NOT NULL,
  end_seconds DOUBLE PRECISION NOT NULL,
  object_key VARCHAR(1024),
  srt_object_key VARCHAR(1024),
  status VARCHAR(32) NOT NULL DEFAULT 'clipping',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_users_supabase_id ON users(supabase_id);
CREATE INDEX IF NOT EXISTS ix_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS ix_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS ix_jobs_video_id ON jobs(video_id);
CREATE INDEX IF NOT EXISTS ix_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS ix_transcripts_video_id ON transcripts(video_id);
CREATE INDEX IF NOT EXISTS ix_clips_video_id ON clips(video_id);
CREATE INDEX IF NOT EXISTS ix_clips_user_id ON clips(user_id);
CREATE INDEX IF NOT EXISTS ix_clips_status ON clips(status);

