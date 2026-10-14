/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { GitPullRequest, ArrowLeft } from "lucide-react";

export default async function RepoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const id = resolvedParams.id;
  let repo = null;
  let prs: any[] = [];
  try {
    repo = await ApiService.getRepo(id);
    prs = await ApiService.getPrs(id);
  } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
    console.error(err);
  }

  if (!repo) {
    return <div className="p-6">Repository not found or error loading data.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/dashboard/repos"><ArrowLeft className="h-5 w-5" /></Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{repo.owner}/{repo.name}</h1>
          <p className="text-muted-foreground mt-1">Status: {repo.sync_status} · Branch: {repo.default_branch}</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><GitPullRequest className="h-5 w-5" /> Pull Requests</CardTitle>
          </CardHeader>
          <CardContent>
            {prs.length === 0 ? (
              <p className="text-sm text-muted-foreground">No Pull Requests found.</p>
            ) : (
              <ul className="space-y-4">
                {prs.map(pr => (
                  <li key={pr.id} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{pr.title}</p>
                        <p className="text-xs text-muted-foreground mt-1">Author: {pr.author} · Status: {pr.state}</p>
                        <p className="text-xs text-muted-foreground mt-1 text-emerald-600">
                          +{pr.additions} -{pr.deletions} ({pr.changed_files} files)
                        </p>
                      </div>
                      <Button variant="secondary" size="sm" asChild>
                        <Link href={`/dashboard/repos/${repo.id}/pr/${pr.id}`}>Predict</Link>
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
