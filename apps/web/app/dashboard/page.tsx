import type { Metadata } from "next";

import { SystemStatus } from "@/components/system-status";
import { fetchHealth, serverApiBaseUrl } from "@/lib/api";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Live state of the GitSync Studio platform.",
};

// The health report is live state: never prerender it at build time, never cache
// it. Without this, `next build` would try to reach the API from the build box.
export const dynamic = "force-dynamic";

/**
 * PHASE 0 dashboard.
 *
 * It renders the platform's own state, which is exactly what PHASE 0 has to
 * prove: the browser reaches Next.js, Next.js reaches FastAPI on the container
 * network, and FastAPI reaches PostgreSQL, Redis and the Celery worker.
 *
 * PHASE 1 replaces this with the repository list, and this panel moves to
 * /settings.
 */
export default async function DashboardPage() {
  const snapshot = await fetchHealth();

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Platform status</h1>
        <p className="text-sm text-muted-foreground">
          Served by <code className="font-mono">{serverApiBaseUrl()}/api/v1/health</code>, read
          fresh on every request.
        </p>
      </header>

      <SystemStatus snapshot={snapshot} />
    </div>
  );
}
