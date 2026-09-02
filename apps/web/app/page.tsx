import Link from "next/link";

import { Boxes, FileText, GitPullRequest } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const CAPABILITIES = [
  {
    icon: GitPullRequest,
    title: "Pull request merge predictor",
    description:
      "Advisory merge probability, an expected time bucket, a confidence figure and the reasons behind them. Trained on your repository's own history with a temporal split.",
    phase: "PHASE 3",
  },
  {
    icon: Boxes,
    title: "Drive-backed large files",
    description:
      "SHA-256 content addressing with deduplication and resumable Google Drive uploads. Git stores a pointer; the binary lives in Drive.",
    phase: "PHASE 4",
  },
  {
    icon: FileText,
    title: "Grounded README generator",
    description:
      "Every claim traced to repository evidence, warnings for anything unverified, and a human approval gate before a single byte is written.",
    phase: "PHASE 5",
  },
] as const;

export default function Home() {
  return (
    <div className="flex flex-col gap-10">
      <section className="flex flex-col gap-4">
        <p className="font-mono text-xs tracking-widest text-muted-foreground uppercase">
          Phase 0 · Foundation
        </p>
        <h1 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
          Repository intelligence for teams that review their own work
        </h1>
        <p className="max-w-2xl text-base text-muted-foreground">
          GitSync Studio reads a repository&apos;s history and tells you what it actually says:
          which pull requests are likely to land, where the large files went, and what the README
          can honestly claim. The foundation is in place - the platform boots, the services talk to
          each other, and every feature lands in its own phase behind tests.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/dashboard">Open the dashboard</Link>
          </Button>
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="font-heading text-xl font-medium">What is being built</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map(({ icon: Icon, title, description, phase }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="size-4 text-muted-foreground" aria-hidden />
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="font-mono text-xs text-muted-foreground">{phase}</span>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
