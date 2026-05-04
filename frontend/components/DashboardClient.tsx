"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Clapperboard, FileVideo, RefreshCw } from "lucide-react";
import clsx from "clsx";
import { AuthBar } from "@/components/AuthBar";
import { ClipGrid } from "@/components/ClipGrid";
import { StatusBadge } from "@/components/StatusBadge";
import { UploadPanel } from "@/components/UploadPanel";
import { getVideo, listVideos } from "@/lib/api";
import type { CreatedVideo, VideoDetail, VideoListItem } from "@/types/api";

function isProcessing(status: string) {
  return !["completed", "failed"].includes(status);
}

function progressFor(video: VideoListItem | VideoDetail) {
  const latest = "latest_job" in video ? video.latest_job : video.jobs?.[0];
  if (latest) return Math.round(latest.progress);
  return video.status === "completed" ? 100 : 0;
}

export function DashboardClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [videos, setVideos] = useState<VideoListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get("video"));
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedSummary = useMemo(
    () => videos.find((video) => video.id === selectedId) ?? null,
    [selectedId, videos]
  );

  const refresh = useCallback(async () => {
    setError("");
    try {
      const nextVideos = await listVideos();
      setVideos(nextVideos);
      const targetId = selectedId || searchParams.get("video") || nextVideos[0]?.id || null;
      if (targetId) {
        setSelectedId(targetId);
        setDetail(await getVideo(targetId));
      } else {
        setDetail(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load dashboard");
    } finally {
      setLoading(false);
    }
  }, [searchParams, selectedId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const shouldPoll =
      videos.some((video) => isProcessing(video.status)) || (detail ? isProcessing(detail.status) : false);
    if (!shouldPoll) return;
    const timer = window.setInterval(refresh, 4000);
    return () => window.clearInterval(timer);
  }, [detail, refresh, videos]);

  function selectVideo(videoId: string) {
    setSelectedId(videoId);
    router.replace(`/dashboard?video=${videoId}`);
  }

  function created(video: CreatedVideo) {
    setSelectedId(video.video_id);
    router.replace(`/dashboard?video=${video.video_id}`);
    refresh();
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-white/10 bg-ink/90">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-5">
          <Link className="flex items-center gap-2 font-black text-white" href="/">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-emerald-300 text-zinc-950">
              <Clapperboard className="h-5 w-5" />
            </span>
            ClipForge
          </Link>
          <AuthBar />
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[340px_1fr]">
        <aside className="space-y-4">
          <UploadPanel onCreated={created} />

          <div className="rounded-lg border border-white/10 bg-panel">
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <h2 className="font-semibold text-white">Videos</h2>
              <button
                className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 text-zinc-300 hover:bg-white/10"
                onClick={refresh}
                aria-label="Refresh videos"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-[62vh] overflow-y-auto p-2">
              {loading ? <p className="p-3 text-sm text-zinc-400">Loading videos...</p> : null}
              {!loading && !videos.length ? <p className="p-3 text-sm text-zinc-400">No videos yet.</p> : null}
              {videos.map((video) => (
                <button
                  key={video.id}
                  className={clsx(
                    "focus-ring mb-2 w-full rounded-md border p-3 text-left transition",
                    selectedId === video.id
                      ? "border-emerald-300/50 bg-emerald-300/10"
                      : "border-white/10 bg-white/5 hover:bg-white/10"
                  )}
                  onClick={() => selectVideo(video.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-zinc-950 text-zinc-300">
                      <FileVideo className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-white">
                        {video.filename || video.source_url || "Untitled video"}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <StatusBadge status={video.status} />
                        <span className="text-xs text-zinc-500">{video.clip_count} clips</span>
                      </div>
                      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-emerald-300"
                          style={{ width: `${progressFor(video)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <section className="min-w-0 space-y-5">
          {error ? <div className="rounded-lg border border-rose-300/30 bg-rose-300/10 p-4 text-rose-100">{error}</div> : null}

          {detail ? (
            <>
              <div className="rounded-lg border border-white/10 bg-panel p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h1 className="text-2xl font-black text-white">
                        {detail.filename || detail.source_url || "Video"}
                      </h1>
                      <StatusBadge status={detail.status} />
                    </div>
                    <p className="mt-2 text-sm text-zinc-400">
                      {detail.duration_seconds ? `${Math.round(detail.duration_seconds)} seconds` : "Duration pending"}
                      {selectedSummary ? ` · ${selectedSummary.clip_count} generated clips` : ""}
                    </p>
                    {detail.error_message ? <p className="mt-3 text-sm text-rose-300">{detail.error_message}</p> : null}
                  </div>
                  <div className="min-w-48">
                    <div className="mb-2 flex justify-between text-xs text-zinc-400">
                      <span>Progress</span>
                      <span>{progressFor(detail)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/10">
                      <div className="h-full rounded-full bg-emerald-300" style={{ width: `${progressFor(detail)}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              <ClipGrid clips={detail.clips} />
            </>
          ) : (
            <div className="rounded-lg border border-white/10 bg-panel p-10 text-center">
              <h1 className="text-2xl font-black text-white">Your clips dashboard</h1>
              <p className="mt-3 text-zinc-400">Upload a video or paste a URL to start a new processing job.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

