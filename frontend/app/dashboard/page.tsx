import { Suspense } from "react";
import { DashboardClient } from "@/components/DashboardClient";

export default function DashboardPage() {
  return (
    <Suspense fallback={<main className="p-6 text-zinc-300">Loading dashboard...</main>}>
      <DashboardClient />
    </Suspense>
  );
}

