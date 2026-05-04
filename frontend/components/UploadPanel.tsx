"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { HardDrive, Link2, Loader2, UploadCloud } from "lucide-react";
import { createVideoFromLocal, createVideoFromUrl, uploadVideo } from "@/lib/api";
import type { CreatedVideo } from "@/types/api";

export function UploadPanel({ onCreated }: { onCreated: (video: CreatedVideo) => void }) {
  const [url, setUrl] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file && !url && !localPath) return;
    setBusy(true);
    setError("");
    try {
      const created = file
        ? await uploadVideo(file)
        : localPath
          ? await createVideoFromLocal(localPath)
          : await createVideoFromUrl(url);
      setUrl("");
      setLocalPath("");
      setFile(null);
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  return (
    <form className="rounded-lg border border-white/10 bg-panel p-4 shadow-glow" onSubmit={submit}>
      <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <label className="relative">
          <Link2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            className="focus-ring h-12 w-full rounded-md border border-white/10 bg-white/5 pl-10 pr-3 text-sm text-white placeholder:text-zinc-500"
            placeholder="Paste YouTube or video URL"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            disabled={busy || Boolean(file) || Boolean(localPath)}
          />
        </label>
        <label className="focus-within:outline-emerald-300 inline-flex h-12 cursor-pointer items-center justify-center gap-2 rounded-md border border-white/10 px-4 text-sm font-medium text-zinc-200 hover:bg-white/10">
          <UploadCloud className="h-4 w-4" />
          {file ? file.name : "Upload video"}
          <input
            className="sr-only"
            type="file"
            accept="video/*"
            onChange={onFileChange}
            disabled={busy || Boolean(url) || Boolean(localPath)}
          />
        </label>
        <button
          className="focus-ring inline-flex h-12 items-center justify-center gap-2 rounded-md bg-emerald-300 px-5 text-sm font-bold text-zinc-950 hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={busy || (!file && !url && !localPath)}
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Create clips
        </button>
      </div>
      <label className="relative mt-3 block">
        <HardDrive className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          className="focus-ring h-11 w-full rounded-md border border-white/10 bg-white/5 pl-10 pr-3 text-sm text-white placeholder:text-zinc-500"
          placeholder="Local sample video path"
          value={localPath}
          onChange={(event) => setLocalPath(event.target.value)}
          disabled={busy || Boolean(file) || Boolean(url)}
        />
      </label>
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </form>
  );
}
