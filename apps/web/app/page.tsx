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
    <div className="flex flex-col gap-16 min-h-screen bg-gradient-to-b from-background to-muted/20 pb-20">
      <section className="flex flex-col gap-6 items-center text-center pt-24 pb-12 px-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 fill-mode-both">
        <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 animate-in fade-in zoom-in duration-700 delay-200 fill-mode-both">🚀 Phase 0 · Foundation</div>
        <p className="font-mono text-xs tracking-widest text-muted-foreground uppercase sr-only">
          Phase 0 · Foundation
        </p>
        <h1 className="font-heading text-5xl font-extrabold tracking-tight sm:text-6xl md:text-7xl bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">
          Repository intelligence for teams that review their own work
        </h1>
        <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">
          GitSync Studio reads a repository&apos;s history and tells you what it actually says:
          which pull requests are likely to land, where the large files went, and what the README
          can honestly claim. The foundation is in place - the platform boots, the services talk to
          each other, and every feature lands in its own phase behind tests.
        </p>
        <div className="flex flex-wrap gap-4 justify-center mt-6 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300 fill-mode-both">
          <Button asChild size="lg" className="rounded-full px-8 shadow-lg hover:shadow-xl transition-all">
            <Link href="/dashboard">Open the dashboard</Link>
          </Button>
        </div>
      </section>

      <section className="flex flex-col gap-8 px-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500 fill-mode-both">
        <h2 className="font-heading text-xl font-medium">What is being built</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map(({ icon: Icon, title, description, phase }) => (
            <Card key={title} className="group flex flex-col h-full hover:shadow-md transition-all hover:border-primary/50 overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110 duration-500 pointer-events-none">
                <Icon className="w-32 h-32 -mr-6 -mt-6" aria-hidden />
              </div>
              <CardHeader className="flex-1">
                <Icon className="size-6 text-primary mb-2" aria-hidden />
                <CardTitle className="text-xl">{title}</CardTitle>
                <CardDescription className="text-sm leading-relaxed">{description}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto pt-0">
                <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary/50 text-secondary-foreground">
                  {phase}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
