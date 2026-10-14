const fs = require('fs');
const path = require('path');
const webPath = path.join(__dirname, 'apps/web');

// Update API Service to add PR listing
const apiServicePath = path.join(webPath, 'lib/api-service.ts');
let apiServiceCode = fs.readFileSync(apiServicePath, 'utf-8');
if (!apiServiceCode.includes('getPrs')) {
  apiServiceCode = apiServiceCode.replace(
    /getRepo:\s*\([^)]*\)\s*=>[^,]*,/g, 
    match => \`\${match}\n  getPrs: (repoId: string): Promise<any[]> => fetchApi(\\\`/api/v1/repos/\\\${repoId}/prs\\\`, { cache: "no-store" }),\`
  );
  fs.writeFileSync(apiServicePath, apiServiceCode);
}

// Scaffold repo detail page
const repoDetailCode = `
import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { GitPullRequest, ArrowLeft } from "lucide-react";

export default async function RepoDetailPage({ params }: { params: { id: string } }) {
  let repo = null;
  let prs = [];
  try {
    repo = await ApiService.getRepo(params.id);
    prs = await ApiService.getPrs(params.id);
  } catch (err) {
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
                        <Link href={\`/dashboard/repos/\${repo.id}/pr/\${pr.id}\`}>Predict</Link>
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
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/repos/[id]/page.tsx'), repoDetailCode);

// Scaffold PR Prediction Page
fs.mkdirSync(path.join(webPath, 'app/dashboard/repos/[id]/pr/[prId]'), { recursive: true });
const prPredictionCode = `
import { ApiService } from "@/lib/api-service";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft, BrainCircuit, Clock, GitMerge } from "lucide-react";

export default async function PrPredictionPage({ params }: { params: { id: string, prId: string } }) {
  let prediction = null;
  let errorMsg = null;
  try {
    prediction = await ApiService.getPrediction(params.prId);
  } catch (err: any) {
    console.error(err);
    errorMsg = err.message;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href={\`/dashboard/repos/\${params.id}\`}><ArrowLeft className="h-5 w-5" /></Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PR Intelligence</h1>
          <p className="text-muted-foreground mt-1">ML Merge Prediction</p>
        </div>
      </div>

      {errorMsg ? (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-6 text-destructive">
            Failed to load prediction: {errorMsg}
          </CardContent>
        </Card>
      ) : prediction ? (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><GitMerge className="h-5 w-5 text-primary" /> Merge Probability</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-6">
                <span className="text-6xl font-bold tracking-tighter text-primary">
                  {(prediction.mergeProbability * 100).toFixed(1)}%
                </span>
                <span className="text-muted-foreground mt-2 font-medium">Confidence: {(prediction.confidence * 100).toFixed(0)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BrainCircuit className="h-5 w-5" /> Prediction Explanations</CardTitle>
              <CardDescription>Why the model made this prediction</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {prediction.reasons?.map((r: string, idx: number) => (
                  <li key={idx} className="flex items-center gap-2 bg-muted/50 p-2 rounded text-sm">
                    <span className="text-primary font-bold">+</span> {r.replace(/_/g, " ")}
                  </li>
                ))}
              </ul>
              <div className="mt-6 flex items-center gap-2 border-t pt-4">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Expected Time Bucket: <span className="text-primary">{prediction.mergeTimeBucket}</span></span>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="p-6">Loading...</div>
      )}
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/repos/[id]/pr/[prId]/page.tsx'), prPredictionCode);

// Scaffold README generator
const readmeGeneratorCode = `
"use client";
import { useState } from "react";
import { fetchApi } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function ReadmeGeneratorPage() {
  const [repoPath, setRepoPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!repoPath) return;
    
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await fetchApi("/api/v1/readme/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate README");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">README Generator</h1>
        <p className="text-muted-foreground mt-2">Generate evidence-grounded documentation.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Analyze Repository</CardTitle>
          <CardDescription>Enter an absolute local path to a repository workspace to extract evidence.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleGenerate} className="flex gap-4">
            <input 
              type="text" 
              value={repoPath} 
              onChange={e => setRepoPath(e.target.value)} 
              placeholder="/absolute/path/to/repo" 
              className="flex-1 px-3 py-2 border rounded-md bg-background text-sm"
              required
            />
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Analyze & Generate
            </Button>
          </form>
          {error && <p className="text-destructive text-sm mt-3">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle className="text-lg">Extracted Evidence</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {result.evidence?.architecture?.framework && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Detected Framework: {result.evidence.architecture.framework}
                  </li>
                )}
                {Object.keys(result.evidence?.scripts || {}).length > 0 && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Detected {Object.keys(result.evidence.scripts).length} NPM scripts
                  </li>
                )}
              </ul>
              {result.warnings?.map((w: any, idx: number) => (
                <div key={idx} className="mt-4 p-3 bg-amber-500/10 text-amber-600 rounded-md flex items-start gap-2 text-sm">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">{w.type}</span>
                    {w.message}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2"><FileText className="h-5 w-5" /> README Draft</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border rounded-md">
                <div className="bg-muted px-4 py-2 border-b flex justify-between items-center text-sm font-medium">
                  README.md
                  <Button variant="outline" size="sm">Approve & Save</Button>
                </div>
                <textarea 
                  className="w-full h-[400px] p-4 bg-background font-mono text-sm resize-none focus:outline-none"
                  defaultValue={result.draft}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
`;
fs.writeFileSync(path.join(webPath, 'app/dashboard/readme/page.tsx'), readmeGeneratorCode);

console.log("Features scaffolded.");
