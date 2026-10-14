/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, GitPullRequest } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function DashboardPage() {
  let user = null;
  let repos: any[] = [];
  try {
    user = await ApiService.getMe();
    repos = await ApiService.getRepos();
  } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
    console.error(err);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome back, {user?.name || user?.email || "User"}.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connected Repositories</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{repos.length}</div>
          </CardContent>
        </Card>
      </div>

      {repos.length === 0 ? (
        <Card className="border-dashed bg-muted/50 text-center py-12">
          <CardContent className="flex flex-col items-center justify-center">
            <Database className="h-8 w-8 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No repositories connected yet.</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Connect your GitHub account to sync repositories.
            </p>
            <Button asChild>
              <Link href="/login">Connect GitHub</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Recent Repositories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {repos.map((repo) => (
                <div key={repo.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div>
                    <Link href={`/dashboard/repos/${repo.id}`} className="font-medium hover:underline">
                      {repo.owner}/{repo.name}
                    </Link>
                    <p className="text-sm text-muted-foreground">Status: {repo.sync_status}</p>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/dashboard/repos/${repo.id}`}>View</Link>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
