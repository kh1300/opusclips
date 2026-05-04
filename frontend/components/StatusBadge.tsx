import clsx from "clsx";
import type { JobStatus } from "@/types/api";

const labels: Record<JobStatus, string> = {
  uploaded: "Uploaded",
  transcribing: "Transcribing",
  analyzing: "Analyzing",
  clipping: "Clipping",
  subtitling: "Subtitling",
  completed: "Completed",
  failed: "Failed"
};

const tones: Record<JobStatus, string> = {
  uploaded: "border-white/10 bg-white/10 text-zinc-200",
  transcribing: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  analyzing: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  clipping: "border-fuchsia-300/30 bg-fuchsia-300/10 text-fuchsia-100",
  subtitling: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  completed: "border-emerald-300/40 bg-emerald-300/15 text-emerald-100",
  failed: "border-rose-300/40 bg-rose-300/15 text-rose-100"
};

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span className={clsx("inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium", tones[status])}>
      {labels[status]}
    </span>
  );
}
