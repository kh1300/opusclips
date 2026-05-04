export type JobStatus =
  | "uploaded"
  | "transcribing"
  | "analyzing"
  | "clipping"
  | "subtitling"
  | "completed"
  | "failed";

export type Job = {
  id: string;
  video_id: string;
  status: JobStatus;
  progress: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type Clip = {
  id: string;
  video_id: string;
  title: string;
  hook?: string | null;
  reason?: string | null;
  caption?: string | null;
  start_time: string;
  end_time: string;
  start_seconds: number;
  end_seconds: number;
  status: JobStatus | "clipping";
  download_url?: string | null;
  created_at: string;
};

export type VideoListItem = {
  id: string;
  source_type: "upload" | "url" | "local";
  source_url?: string | null;
  filename?: string | null;
  status: JobStatus;
  error_message?: string | null;
  clip_count: number;
  latest_job?: Job | null;
  created_at: string;
  updated_at: string;
};

export type VideoDetail = {
  id: string;
  source_type: "upload" | "url" | "local";
  source_url?: string | null;
  filename?: string | null;
  status: JobStatus;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  duration_seconds?: number | null;
  clips: Clip[];
  jobs: Job[];
  transcript?: { text: string; language?: string | null } | null;
};

export type CreatedVideo = {
  video_id: string;
  job_id: string;
  status: JobStatus;
};
