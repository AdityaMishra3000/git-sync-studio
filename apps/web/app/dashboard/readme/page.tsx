"use client";

import { useEffect, useState } from "react";
import {
  approveReadmeAction,
  generateReadmeAction,
  getConnectedReposAction,
  regenerateSectionAction,
  saveReadmeAction,
} from "./actions";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  CheckCircle2,
  Copy,
  Cpu,
  Download,
  Eye,
  FileCode,
  FileText,
  Layers,
  Loader2,
  RefreshCw,
  Save,
  ShieldCheck,
  
} from "lucide-react";

interface ValidationFinding {
  severity: "error" | "warning" | "info";
  dimension: string;
  section: string;
  explanation: string;
  suggested_correction: string;
}

interface ValidationResult {
  score: number;
  dimension_scores: Record<string, number>;
  findings: ValidationFinding[];
  is_valid: boolean;
  has_unverified_claims: boolean;
}

interface RepositoryEvidence {
  name: string;
  description?: string;
  primary_language?: string;
  languages: Record<string, number>;
  frameworks: string[];
  package_managers: string[];
  is_monorepo: boolean;
  monorepo_workspaces: string[];
  commands: Array<{ category: string; command: string; description: string; verified: boolean }>;
  environment_variables: Array<{ name: string; purpose: string; required: boolean; example_value?: string }>;
  architecture_components: Array<{ name: string; role: string; technologies: string[] }>;
  relationships: Array<{ source: string; target: string; relationship_type: string; description: string }>;
  endpoints: Array<{ path: string; method: string; summary?: string; auth_required: boolean }>;
  database_technologies: string[];
  background_workers: string[];
  services: Array<{ name: string; ports: string[] }>;
  tests: {
    frameworks: string[];
    test_dirs: string[];
    has_unit_tests: boolean;
    has_integration_tests: boolean;
    has_e2e_tests: boolean;
  };
  license_type?: string;
  missing_evidence: string[];
}

export default function ReadmeGeneratorPage() {
  const [repoPath, setRepoPath] = useState("/home/adityam/Aditya.m/College/git-sync-studio");
  const [selectedRepoId, setSelectedRepoId] = useState<string>("");
  const [detailLevel, setDetailLevel] = useState<"detailed" | "standard" | "minimal">("detailed");
  const [loading, setLoading] = useState(false);
  const [regeneratingSection, setRegeneratingSection] = useState(false);
  const [selectedSection, setSelectedSection] = useState<string>("overview");

  const [connectedRepos, setConnectedRepos] = useState<Array<{ id: string; name: string; owner: string }>>([]);
  const [result, setResult] = useState<{
    draft: string;
    sections: Record<string, string>;
    evidence: RepositoryEvidence;
    validation: ValidationResult;
    status: string;
    draft_id?: string;
  } | null>(null);

  const [draftContent, setDraftContent] = useState("");
  const [viewMode, setViewMode] = useState<"editor" | "preview">("preview");
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [documentStatus, setDocumentStatus] = useState<"draft" | "edited" | "approved">("draft");

  useEffect(() => {
    getConnectedReposAction().then((repos) => {
      if (Array.isArray(repos) && repos.length > 0) {
        setConnectedRepos(repos);
      }
    });
  }, []);

  async function handleGenerate(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!repoPath) return;

    setLoading(true);
    setError("");
    setStatusMessage("Extracting repository evidence and generating documentation...");
    try {
      const data = await generateReadmeAction(repoPath, selectedRepoId || undefined, detailLevel);
      setResult(data);
      setDraftContent(data.draft);
      setDocumentStatus("draft");
      setStatusMessage("README generated and validated.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate README";
      setError(msg);
      setStatusMessage("");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegenerateSection() {
    if (!result || !repoPath) return;
    setRegeneratingSection(true);
    setStatusMessage(`Regenerating section '${selectedSection}'...`);
    try {
      const data = await regenerateSectionAction(repoPath, selectedSection, draftContent, detailLevel);
      setDraftContent(data.draft);
      setResult((prev) => (prev ? { ...prev, draft: data.draft, sections: data.sections, validation: data.validation } : null));
      setDocumentStatus("edited");
      setStatusMessage(`Section '${selectedSection}' regenerated.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to regenerate section";
      setError(msg);
    } finally {
      setRegeneratingSection(false);
    }
  }

  async function handleSaveDraft() {
    if (!repoPath || !draftContent) return;
    setStatusMessage("Saving draft...");
    try {
      await saveReadmeAction(repoPath, draftContent, selectedRepoId || undefined, "draft");
      setDocumentStatus("draft");
      setStatusMessage("README draft saved to workspace.");
      setTimeout(() => setStatusMessage(""), 3500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save draft";
      setError(msg);
    }
  }

  async function handleApprove() {
    if (!repoPath || !draftContent) return;
    setStatusMessage("Approving and saving documentation...");
    try {
      await approveReadmeAction(repoPath, draftContent, selectedRepoId || undefined);
      setDocumentStatus("approved");
      setStatusMessage("Documentation approved and written to README.md!");
      setTimeout(() => setStatusMessage(""), 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve documentation";
      setError(msg);
    }
  }

  function handleContentChange(val: string) {
    setDraftContent(val);
    if (documentStatus !== "edited") {
      setDocumentStatus("edited");
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(draftContent);
    setStatusMessage("Copied Markdown to clipboard!");
    setTimeout(() => setStatusMessage(""), 2500);
  }

  function downloadReadme() {
    const blob = new Blob([draftContent], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "README.md";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Evidence-Grounded README Generator</h1>
          <p className="text-muted-foreground mt-1">
            Analyze codebase architecture, execution commands, and configuration to generate production-quality technical documentation.
          </p>
        </div>
        {documentStatus === "approved" && (
          <Badge variant="default" className="bg-emerald-600 text-white self-start md:self-auto py-1 px-3 text-sm">
            <CheckCircle2 className="h-4 w-4 mr-1.5" /> Approved & Saved
          </Badge>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" /> Repository Selection & Detail Level
          </CardTitle>
          <CardDescription>
            Select from connected repositories or provide an absolute host workspace path.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {connectedRepos.length > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Connected Repos:</span>
              <div className="flex flex-wrap gap-2">
                {connectedRepos.map((repo) => (
                  <button
                    key={repo.id}
                    type="button"
                    onClick={() => {
                      setSelectedRepoId(repo.id);
                      setRepoPath(`/home/adityam/Aditya.m/College/${repo.name}`);
                    }}
                    className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                      selectedRepoId === repo.id
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-muted/50 hover:bg-muted text-foreground border-border"
                    }`}
                  >
                    {repo.owner}/{repo.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={repoPath}
              onChange={(e) => {
                setRepoPath(e.target.value);
                setSelectedRepoId("");
              }}
              placeholder="/absolute/path/to/workspace"
              className="flex-1 px-3 py-2 border rounded-md bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />

            <div className="flex items-center rounded-md border border-input bg-background p-1">
              {(["detailed", "standard", "minimal"] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setDetailLevel(level)}
                  className={`capitalize px-3 py-1 text-xs font-medium rounded transition-colors ${
                    detailLevel === level ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>

            <Button type="submit" disabled={loading} className="min-w-[170px]">
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Analyze & Generate
            </Button>
          </form>

          {error && <p className="text-destructive text-sm font-medium">{error}</p>}
          {statusMessage && <p className="text-muted-foreground text-xs">{statusMessage}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Column: Evidence & Validation Findings (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Scorecard */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-primary" /> Documentation Quality Score
                  </CardTitle>
                  <span
                    className={`text-xl font-bold px-2.5 py-0.5 rounded-full ${
                      result.validation.score >= 80
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : result.validation.score >= 60
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                        : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                    }`}
                  >
                    {result.validation.score}/100
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(result.validation.dimension_scores).map(([dim, score]) => (
                    <div key={dim} className="flex justify-between p-2 rounded bg-muted/40 border">
                      <span className="capitalize text-muted-foreground">{dim.replace(/_/g, " ")}:</span>
                      <span className="font-semibold">{score} pts</span>
                    </div>
                  ))}
                </div>

                {result.validation.findings.length > 0 && (
                  <div className="space-y-2 mt-4 pt-3 border-t">
                    <span className="text-xs font-semibold text-muted-foreground uppercase">Validation Findings:</span>
                    <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                      {result.validation.findings.map((f, idx) => (
                        <div
                          key={idx}
                          className={`p-2.5 rounded text-xs border ${
                            f.severity === "error"
                              ? "bg-red-500/10 border-red-500/30 text-red-600 dark:text-red-400"
                              : f.severity === "warning"
                              ? "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400"
                              : "bg-blue-500/10 border-blue-500/30 text-blue-600"
                          }`}
                        >
                          <div className="flex items-center gap-1.5 font-semibold">
                            <AlertCircle className="h-3.5 w-3.5" />
                            <span className="uppercase">{f.dimension}</span> · <span>[{f.section}]</span>
                          </div>
                          <p className="mt-1">{f.explanation}</p>
                          <p className="mt-1 text-[11px] opacity-80">Fix: {f.suggested_correction}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Extracted Evidence Details */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-primary" /> Verified Technical Evidence
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-0 text-sm">
                <div>
                  <span className="text-xs font-semibold uppercase text-muted-foreground block mb-1">Ecosystem & Languages</span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.evidence.primary_language && (
                      <Badge variant="secondary" className="font-medium">
                        Primary: {result.evidence.primary_language}
                      </Badge>
                    )}
                    {Object.entries(result.evidence.languages).map(([lang, pct]) => (
                      <Badge key={lang} variant="outline" className="text-xs">
                        {lang} {pct}%
                      </Badge>
                    ))}
                  </div>
                </div>

                {result.evidence.frameworks.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold uppercase text-muted-foreground block mb-1">Detected Frameworks</span>
                    <div className="flex flex-wrap gap-1.5">
                      {result.evidence.frameworks.map((fw) => (
                        <Badge key={fw} variant="default" className="text-xs">
                          {fw}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {result.evidence.architecture_components.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold uppercase text-muted-foreground block mb-1">Architecture Components</span>
                    <ul className="space-y-1.5">
                      {result.evidence.architecture_components.map((c, i) => (
                        <li key={i} className="text-xs p-2 rounded bg-muted/40 border">
                          <span className="font-semibold text-foreground">{c.name}</span>
                          <p className="text-muted-foreground mt-0.5">{c.role}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.evidence.commands.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold uppercase text-muted-foreground block mb-1">Inferred Execution Commands</span>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {result.evidence.commands.map((cmd, i) => (
                        <div key={i} className="p-2 rounded bg-muted/50 border text-xs font-mono">
                          <span className="text-primary font-bold">{cmd.category}: </span>
                          <code>{cmd.command}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Markdown Editor & Preview (7 Cols) */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="h-full flex flex-col">
              <CardHeader className="py-3 px-4 border-b flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  <span className="font-semibold text-sm">README.md</span>
                  <Badge variant="outline" className="capitalize text-xs font-normal">
                    {documentStatus}
                  </Badge>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex rounded-md border border-input bg-background p-0.5 mr-2">
                    <button
                      type="button"
                      onClick={() => setViewMode("preview")}
                      className={`px-2.5 py-1 text-xs font-medium rounded flex items-center gap-1 ${
                        viewMode === "preview" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <Eye className="h-3.5 w-3.5" /> Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode("editor")}
                      className={`px-2.5 py-1 text-xs font-medium rounded flex items-center gap-1 ${
                        viewMode === "editor" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <FileCode className="h-3.5 w-3.5" /> Raw
                    </button>
                  </div>

                  <Button variant="ghost" size="icon" onClick={copyToClipboard} title="Copy Markdown">
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={downloadReadme} title="Download README.md">
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleSaveDraft} title="Save to workspace">
                    <Save className="h-4 w-4 mr-1.5" /> Save
                  </Button>
                  <Button variant="default" size="sm" onClick={handleApprove} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                    <CheckCircle2 className="h-4 w-4 mr-1.5" /> Approve
                  </Button>
                </div>
              </CardHeader>

              {/* Section Regenerator Bar */}
              {result.sections && Object.keys(result.sections).length > 0 && (
                <div className="bg-muted/30 px-4 py-2 border-b flex items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Target Section:</span>
                    <select
                      value={selectedSection}
                      onChange={(e) => setSelectedSection(e.target.value)}
                      className="px-2 py-1 rounded border bg-background text-xs font-medium"
                    >
                      {Object.keys(result.sections).map((secKey) => (
                        <option key={secKey} value={secKey}>
                          {secKey.replace(/_/g, " ").toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={regeneratingSection}
                    onClick={handleRegenerateSection}
                    className="h-7 text-xs"
                  >
                    {regeneratingSection ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <RefreshCw className="h-3 w-3 mr-1" />}
                    Regenerate Section
                  </Button>
                </div>
              )}

              <CardContent className="p-0 flex-1 min-h-[550px] flex flex-col">
                {viewMode === "editor" ? (
                  <textarea
                    value={draftContent}
                    onChange={(e) => handleContentChange(e.target.value)}
                    className="w-full flex-1 min-h-[550px] p-4 font-mono text-xs leading-relaxed bg-background resize-none focus:outline-none"
                    placeholder="# README content..."
                  />
                ) : (
                  <div className="p-6 prose prose-neutral dark:prose-invert max-w-none text-sm leading-relaxed overflow-y-auto max-h-[700px] whitespace-pre-wrap font-sans">
                    {draftContent}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
