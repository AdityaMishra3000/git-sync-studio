"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  HardDrive,
  Upload,
  CheckCircle2,
  AlertCircle,
  Copy,
  Download,
  ShieldCheck,
  FileCode,
  Layers,
  Sparkles,
} from "lucide-react";

interface LargeObject {
  id: string;
  repository_id: string;
  oid: string;
  size_bytes: number;
  path: string;
  drive_status: string;
  created_at: string;
}

interface DriveStatus {
  provider: string;
  configured: boolean;
  live_drive_active: boolean;
  storage_root: string;
  total_objects: number;
  total_size_bytes: number;
  unique_blobs: number;
  dedup_savings_bytes: number;
}

interface Repo {
  id: string;
  name: string;
  owner: string;
}

interface Props {
  initialObjects: LargeObject[];
  initialStatus: DriveStatus | null;
  repos: Repo[];
}

function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function LargeFilesClient({ initialObjects, initialStatus, repos }: Props) {
  const [objects, setObjects] = useState<LargeObject[]>(initialObjects);
  const [status, setStatus] = useState<DriveStatus | null>(initialStatus);
  const [selectedRepo, setSelectedRepo] = useState<string>(repos[0]?.id || "");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [customPath, setCustomPath] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [activePointerModal, setActivePointerModal] = useState<{ oid: string; size: number; path: string } | null>(null);
  const [verificationResults, setVerificationResults] = useState<Record<string, { valid: boolean; message: string; loading?: boolean }>>({});
  const [copiedOid, setCopiedOid] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadFile(file);
      if (!customPath) {
        setCustomPath(file.name);
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedRepo) {
      setUploadMessage({ text: "Please select a repository and a file.", type: "error" });
      return;
    }

    setIsUploading(true);
    setUploadMessage(null);

    const formData = new FormData();
    formData.append("repo_id", selectedRepo);
    formData.append("path", customPath || uploadFile.name);
    formData.append("file", uploadFile);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiUrl}/drive/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Upload failed");
      }

      const result = await res.json();
      setUploadMessage({
        text: result.reused
          ? `File deduplicated! Reusing existing stored blob with SHA-256: ${result.oid.substring(0, 12)}...`
          : `File successfully uploaded to ${status?.provider === "google_drive" ? "Google Drive" : "Local Storage"}!`,
        type: "success",
      });

      // Show pointer modal
      setActivePointerModal({
        oid: result.oid,
        size: result.size_bytes,
        path: result.path,
      });

      // Refresh list & status
      const listRes = await fetch(`${apiUrl}/drive`);
      if (listRes.ok) {
        const updatedList = await listRes.json();
        setObjects(updatedList);
      }

      const statusRes = await fetch(`${apiUrl}/drive/status`);
      if (statusRes.ok) {
        const updatedStatus = await statusRes.json();
        setStatus(updatedStatus);
      }

      // Reset form
      setUploadFile(null);
      setCustomPath("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setUploadMessage({ text: `Upload error: ${msg}`, type: "error" });
    } finally {
      setIsUploading(false);
    }
  };

  const verifyObject = async (oid: string) => {
    setVerificationResults((prev) => ({
      ...prev,
      [oid]: { valid: false, message: "Verifying checksum...", loading: true },
    }));

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiUrl}/drive/verify/${oid}`, { method: "POST" });
      const data = await res.json();

      setVerificationResults((prev) => ({
        ...prev,
        [oid]: {
          valid: data.valid,
          message: data.message || (data.valid ? "Verified bit-for-bit SHA-256 match" : "Verification failed"),
          loading: false,
        },
      }));
    } catch {
      setVerificationResults((prev) => ({
        ...prev,
        [oid]: { valid: false, message: "Verification check unreachable", loading: false },
      }));
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedOid(id);
    setTimeout(() => setCopiedOid(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header and Storage Provider Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Large Files Storage</h1>
          <p className="text-muted-foreground mt-1">
            Git-LFS-inspired large binary tracking backed by Google Drive & local content-addressed storage.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status?.live_drive_active ? (
            <Badge className="bg-emerald-500/15 text-emerald-700 hover:bg-emerald-500/20 border-emerald-500/30 flex items-center gap-1.5 py-1 px-3">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Google Drive (Live Active)
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/30 flex items-center gap-1.5 py-1 px-3">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              Local Storage Fallback Mode
            </Badge>
          )}
        </div>
      </div>

      {/* Storage Provider Explanation Banner */}
      {!status?.live_drive_active && (
        <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 text-sm text-blue-900 dark:border-blue-950 dark:bg-blue-950/20 dark:text-blue-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold">Local Content-Addressed Storage Active</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">
                Google Drive credentials are not configured in this environment. The system operates fully using
                deterministic content-addressed storage located at{" "}
                <code className="bg-blue-100 dark:bg-blue-900/40 px-1 py-0.5 rounded text-xs font-mono">
                  {status?.storage_root || "/srv/api/.gitsync/storage"}
                </code>
                . Git clean/smudge filters, deduplication, and bit-for-bit SHA-256 integrity verification are 100% operational.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Tracked Files</span>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold">{status?.total_objects ?? objects.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Mapped across repository paths</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Unique Blobs</span>
              <Layers className="h-4 w-4 text-muted-foreground" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold">{status?.unique_blobs ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Content-addressed SHA-256 digests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Deduplication Savings</span>
              <Sparkles className="h-4 w-4 text-emerald-600" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-600">
              {formatBytes(status?.dedup_savings_bytes ?? 0)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {status && status.total_size_bytes > 0
                ? `${Math.round(((status.dedup_savings_bytes || 0) / status.total_size_bytes) * 100)}% space saved`
                : "Zero redundancy"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Total Managed Volume</span>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold">
              {formatBytes(status?.total_size_bytes ?? 0)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Original binary size preserved</p>
          </CardContent>
        </Card>
      </div>

      {/* Upload and Register Large File Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-primary" />
            Upload & Register Large Binary
          </CardTitle>
          <CardDescription>
            Upload a binary file to GitSync storage. The system calculates its SHA-256 OID, deduplicates identical blobs,
            and generates the deterministic Git pointer file for you.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Target Repository</label>
                <select
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={selectedRepo}
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  required
                >
                  {repos.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.owner}/{r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Binary File</label>
                <input
                  type="file"
                  onChange={handleFileChange}
                  className="w-full h-9 text-xs file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 cursor-pointer"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Repository File Path</label>
                <input
                  type="text"
                  placeholder="e.g. assets/model.bin"
                  value={customPath}
                  onChange={(e) => setCustomPath(e.target.value)}
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  required
                />
              </div>
            </div>

            {uploadMessage && (
              <div
                className={`p-3 rounded-md text-sm flex items-center gap-2 ${
                  uploadMessage.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900"
                    : "bg-red-50 text-red-800 border border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900"
                }`}
              >
                {uploadMessage.type === "success" ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                ) : (
                  <AlertCircle className="h-4 w-4 shrink-0" />
                )}
                <span>{uploadMessage.text}</span>
              </div>
            )}

            <div className="flex justify-end">
              <Button type="submit" disabled={isUploading || !uploadFile} className="gap-2">
                <Upload className="h-4 w-4" />
                {isUploading ? "Uploading & Hashing..." : "Upload & Create Pointer"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Pointer File Modal / Banner if active */}
      {activePointerModal && (
        <Card className="border-primary/40 bg-primary/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2 text-primary">
                <FileCode className="h-5 w-5" />
                Generated Pointer File for {activePointerModal.path}
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActivePointerModal(null)}
                className="text-xs text-muted-foreground"
              >
                Dismiss
              </Button>
            </div>
            <CardDescription>
              Commit this small pointer file to your Git repository instead of the large binary.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <pre className="p-3 rounded-md bg-muted font-mono text-xs overflow-x-auto border">
                {`version https://gitsync.studio/spec/v1\noid sha256:${activePointerModal.oid}\nsize ${activePointerModal.size}\n`}
              </pre>
              <Button
                size="sm"
                variant="secondary"
                className="absolute top-2 right-2 text-xs gap-1"
                onClick={() =>
                  copyToClipboard(
                    `version https://gitsync.studio/spec/v1\noid sha256:${activePointerModal.oid}\nsize ${activePointerModal.size}\n`,
                    "modal"
                  )
                }
              >
                <Copy className="h-3 w-3" />
                {copiedOid === "modal" ? "Copied!" : "Copy Pointer"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Objects Registry Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-primary" /> Objects Registry
          </CardTitle>
          <CardDescription>
            All binary files managed by GitSync Studio with content-addressed SHA-256 digests and storage integrity verification.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/50 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Path</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium">SHA-256 Digest</th>
                  <th className="px-4 py-3 font-medium">Storage Status</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {objects.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-muted-foreground">
                      No large files registered yet. Upload a file above or use the GitSync CLI to track large files.
                    </td>
                  </tr>
                )}
                {objects.map((obj) => {
                  const verification = verificationResults[obj.oid];
                  return (
                    <tr key={obj.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-medium">
                        <div className="flex items-center gap-2">
                          <FileCode className="h-4 w-4 text-muted-foreground shrink-0" />
                          <span>{obj.path}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                        {formatBytes(obj.size_bytes)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        <div className="flex items-center gap-1.5">
                          <span title={obj.oid}>{obj.oid.substring(0, 16)}...</span>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(obj.oid, obj.id)}
                            className="text-muted-foreground hover:text-foreground transition-colors p-1"
                            title="Copy full SHA-256 OID"
                          >
                            <Copy className="h-3 w-3" />
                          </button>
                          {copiedOid === obj.id && (
                            <span className="text-[10px] text-emerald-600 font-sans">Copied!</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium inline-flex items-center gap-1 ${
                            obj.drive_status === "synced"
                              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                              : obj.drive_status === "local_storage"
                              ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                              : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              obj.drive_status === "synced"
                                ? "bg-emerald-500"
                                : obj.drive_status === "local_storage"
                                ? "bg-blue-500"
                                : "bg-amber-500"
                            }`}
                          />
                          {obj.drive_status === "synced"
                            ? "Drive Synced"
                            : obj.drive_status === "local_storage"
                            ? "Local Storage"
                            : "Pending"}
                        </span>
                        {verification && (
                          <div className="text-[11px] mt-1 flex items-center gap-1">
                            {verification.valid ? (
                              <span className="text-emerald-600 flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3" /> {verification.message}
                              </span>
                            ) : verification.loading ? (
                              <span className="text-muted-foreground">Verifying...</span>
                            ) : (
                              <span className="text-red-500 flex items-center gap-1">
                                <AlertCircle className="h-3 w-3" /> {verification.message}
                              </span>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs gap-1"
                            onClick={() => verifyObject(obj.oid)}
                            disabled={verification?.loading}
                          >
                            <ShieldCheck className="h-3.5 w-3.5" />
                            Verify
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs gap-1"
                            asChild
                          >
                            <a
                              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/drive/download/${obj.oid}`}
                              download
                            >
                              <Download className="h-3.5 w-3.5" />
                              Download
                            </a>
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 text-xs gap-1"
                            onClick={() =>
                              setActivePointerModal({
                                oid: obj.oid,
                                size: obj.size_bytes,
                                path: obj.path,
                              })
                            }
                          >
                            Pointer
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
