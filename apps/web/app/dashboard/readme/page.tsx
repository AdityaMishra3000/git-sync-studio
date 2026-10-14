/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

"use client";
import { useState } from "react";
import { generateReadmeAction, saveReadmeAction } from "./actions";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function ReadmeGeneratorPage() {
  const [repoPath, setRepoPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [draftContent, setDraftContent] = useState("");
  const [saveStatus, setSaveStatus] = useState("");
  const [error, setError] = useState("");

  async function handleSave() {
    setSaveStatus("Saving...");
    try {
      await saveReadmeAction(repoPath, draftContent);
      setSaveStatus("Saved successfully!");
      setTimeout(() => setSaveStatus(""), 3000);
    } catch (err: any) {
      if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
      setSaveStatus("Error saving.");
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!repoPath) return;
    
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await generateReadmeAction(repoPath);
      setResult(data);
      setDraftContent(data.draft);
    } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
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
                  <div className="flex items-center gap-2">
    <span className="text-xs text-muted-foreground">{saveStatus}</span>
    <Button variant="outline" size="sm" onClick={handleSave}>Approve & Save</Button>
  </div>
                </div>
                <textarea 
                  className="w-full h-[400px] p-4 bg-background font-mono text-sm resize-none focus:outline-none"
                  value={draftContent} onChange={(e) => setDraftContent(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
