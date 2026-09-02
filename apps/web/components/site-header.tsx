import Link from "next/link";

import { Activity } from "lucide-react";

/**
 * Navigation only lists routes that exist. Repositories, pull requests, files,
 * README and settings arrive with their phases; adding dead links now would only
 * produce 404s in the demo.
 */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-10 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-medium">
          <Activity className="size-4" aria-hidden />
          GitSync Studio
        </Link>
        <nav aria-label="Main">
          <Link
            href="/dashboard"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Dashboard
          </Link>
        </nav>
      </div>
    </header>
  );
}
