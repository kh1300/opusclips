"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight, LayoutDashboard, Link2, Loader2, UploadCloud } from "lucide-react";
import { createVideoFromUrl, uploadVideo } from "@/lib/api";

export function LandingCapture() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!url && !file) return;
    setBusy(true);
    setError("");
    try {
      const result = file ? await uploadVideo(file) : await createVideoFromUrl(url);
      router.push(`/dashboard?video=${result.video_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start processing");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="mt-8 max-w-3xl rounded-lg border border-white/10 bg-white/5 p-3 shadow-glow" onSubmit={submit}>
      <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <label className="relative">
          <Link2 className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-500" />
          <input
            className="focus-ring h-12 w-full rounded-md border border-white/10 bg-zinc-950/80 py-3 pl-11 pr-3 text-white placeholder:text-zinc-500"
            placeholder="Paste a YouTube or video URL"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            disabled={busy || Boolean(file)}
          />
        </label>
        <label className="inline-flex min-h-12 cursor-pointer items-center justify-center gap-2 rounded-md border border-white/10 px-4 text-sm font-semibold text-zinc-100 hover:bg-white/10">
          <UploadCloud className="h-4 w-4" />
          {file ? file.name : "Upload"}
          <input
            className="sr-only"
            type="file"
            accept="video/*"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            disabled={busy || Boolean(url)}
          />
        </label>
        <button
          className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-md bg-emerald-300 px-5 font-bold text-zinc-950 hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={busy || (!url && !file)}
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          Create clips
        </button>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 px-1">
        {error ? <p className="text-sm text-rose-300">{error}</p> : <p className="text-sm text-zinc-500">MP4 uploads and public video URLs are queued for real processing.</p>}
        <Link className="focus-ring inline-flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-white" href="/dashboard">
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </Link>
      </div>
    </form>
  );
}
