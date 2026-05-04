"use client";

import { Download, Film, Sparkles } from "lucide-react";
import type { Clip } from "@/types/api";
import { StatusBadge } from "@/components/StatusBadge";

export function ClipGrid({ clips }: { clips: Clip[] }) {
  if (!clips.length) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 p-8 text-center text-zinc-400">
        Finished clips will appear here as the worker completes each vertical render.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {clips.map((clip) => (
        <article key={clip.id} className="rounded-lg border border-white/10 bg-panel p-3">
          <div className="aspect-[9/16] overflow-hidden rounded-md border border-white/10 bg-zinc-950">
            {clip.download_url ? (
              <video className="h-full w-full object-cover" controls src={clip.download_url} />
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-zinc-500">
                <Film className="h-9 w-9" />
                <StatusBadge status={clip.status === "clipping" ? "clipping" : clip.status} />
              </div>
            )}
          </div>
          <div className="mt-3 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-white">{clip.title}</h3>
                <p className="mt-1 text-xs text-zinc-500">
                  {clip.start_time} - {clip.end_time}
                </p>
              </div>
              <StatusBadge status={clip.status === "clipping" ? "clipping" : clip.status} />
            </div>
            {clip.hook ? (
              <p className="rounded-md border border-amber-300/20 bg-amber-300/10 p-2 text-sm text-amber-50">
                {clip.hook}
              </p>
            ) : null}
            {clip.reason ? (
              <p className="flex gap-2 text-sm text-zinc-400">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                <span>{clip.reason}</span>
              </p>
            ) : null}
            {clip.download_url ? (
              <a
                className="focus-ring inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-white text-sm font-bold text-zinc-950 hover:bg-zinc-200"
                href={clip.download_url}
                download
              >
                <Download className="h-4 w-4" />
                Download
              </a>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}

