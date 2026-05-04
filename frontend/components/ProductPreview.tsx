import { Captions, Clapperboard, Scissors, WandSparkles, type LucideIcon } from "lucide-react";

export function ProductPreview() {
  const steps: Array<[string, string, LucideIcon]> = [
    ["Transcribe", "Whisper creates timestamped segments.", Captions],
    ["Analyze", "GPT ranks hooks, emotion, utility, and pacing.", WandSparkles],
    ["Render", "FFmpeg cuts 9:16 clips with burned subtitles.", Scissors]
  ];

  return (
    <div className="relative mx-auto grid max-w-5xl gap-5 lg:grid-cols-[0.75fr_1fr]">
      <div className="rounded-lg border border-white/10 bg-panel p-4">
        <div className="aspect-[9/16] rounded-md border border-white/10 bg-[linear-gradient(160deg,#0a0a0d_0%,#16171d_42%,#2b151b_100%)] p-4">
          <div className="flex h-full flex-col justify-between">
            <div className="inline-flex w-fit items-center gap-2 rounded-md bg-black/55 px-3 py-2 text-xs text-zinc-200">
              <Clapperboard className="h-4 w-4 text-emerald-300" />
              00:38 viral cut
            </div>
            <div className="space-y-2">
              <div className="w-fit rounded-md bg-white px-3 py-2 text-lg font-black text-zinc-950">
                This changed everything
              </div>
              <div className="w-4/5 rounded-md bg-black/70 px-3 py-2 text-sm text-white">
                Animated subtitles burn in during render
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="grid content-center gap-3">
        {steps.map(([title, body, Icon]) => (
          <div key={String(title)} className="rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-md bg-emerald-300/15 p-2 text-emerald-200">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{title}</h3>
                <p className="mt-1 text-sm text-zinc-400">{body}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
