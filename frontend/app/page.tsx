import Link from "next/link";
import { ArrowRight, Clapperboard } from "lucide-react";
import { LandingCapture } from "@/components/LandingCapture";
import { ProductPreview } from "@/components/ProductPreview";

export default function HomePage() {
  return (
    <main>
      <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5">
        <Link className="flex items-center gap-2 font-black text-white" href="/">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-emerald-300 text-zinc-950">
            <Clapperboard className="h-5 w-5" />
          </span>
          ClipForge
        </Link>
        <Link
          className="focus-ring inline-flex items-center gap-2 rounded-md border border-white/10 px-4 py-2 text-sm font-semibold text-zinc-200 hover:bg-white/10"
          href="/dashboard"
        >
          Dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      </header>

      <section className="mx-auto grid min-h-[calc(100vh-132px)] max-w-7xl content-center gap-12 px-5 pb-10 pt-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div>
          <div className="inline-flex rounded-md border border-emerald-300/30 bg-emerald-300/10 px-3 py-1 text-sm font-semibold text-emerald-100">
            AI shorts studio
          </div>
          <h1 className="mt-6 max-w-4xl text-5xl font-black leading-none text-white md:text-7xl">
            ClipForge
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-300">
            Upload a long video or paste a public video link. The pipeline transcribes, finds high-energy moments,
            renders vertical clips, burns subtitles, and sends the results back to your dashboard.
          </p>
          <LandingCapture />
        </div>
        <ProductPreview />
      </section>
    </main>
  );
}
