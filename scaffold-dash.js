const fs = require('fs');
const path = require('path');

const webPath = path.join(__dirname, 'apps/web');

['app/dashboard/repos', 'app/dashboard/repos/[id]', 'app/dashboard/readme'].forEach(d => {
  fs.mkdirSync(path.join(webPath, d), { recursive: true });
});

const dashPageCode = `
import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, GitPullRequest } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function DashboardPage() {
  let user = null;
  let repos = [];
  try {
    user = await ApiService.getMe();
    repos = await ApiService.getRepos();
  } catch (err) {
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
              <Link href="/api/v1/auth/github/login">Connect GitHub</Link>
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
              {repos.slice(0, 5).map((repo) => (
                <div key={repo.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div>
                    <Link href={\`/dashboard/repos/\${repo.id}\`} className="font-medium hover:underline">
                      {repo.owner}/{repo.name}
                    </Link>
                    <p className="text-sm text-muted-foreground">Status: {repo.sync_status}</p>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={\`/dashboard/repos/\${repo.id}\`}>View</Link>
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
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/page.tsx'), dashPageCode);

const repoListCode = `
import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function ReposPage() {
  let repos = [];
  try {
    repos = await ApiService.getRepos();
  } catch (err) {
    console.error(err);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Repositories</h1>
        <p className="text-muted-foreground mt-2">Manage your connected GitHub repositories.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Repository</th>
                <th className="px-4 py-3 font-medium">Branch</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Last Synced</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {repos.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No repositories found.
                  </td>
                </tr>
              )}
              {repos.map((repo) => (
                <tr key={repo.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">
                    <Link href={\`/dashboard/repos/\${repo.id}\`} className="hover:underline">
                      {repo.owner}/{repo.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{repo.default_branch}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs">
                      {repo.sync_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {repo.last_synced_at ? new Date(repo.last_synced_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={\`/dashboard/repos/\${repo.id}\`}>View Details</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/repos/page.tsx'), repoListCode);

console.log("Dashboard scaffolded.");
