/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

import { fetchServerApi } from "./server-api-client";
import { Repository, User } from "../types/models";

export const ApiService = {
  getMe: (): Promise<User> => fetchServerApi("/api/v1/auth/me", { cache: "no-store" }),
  getLoginUrl: (): Promise<{ url: string }> => fetchServerApi("/api/v1/auth/github/login", { cache: "no-store" }),
  getRepos: (): Promise<Repository[]> => fetchServerApi("/api/v1/repos", { cache: "no-store" }),
  getRepo: (id: string): Promise<Repository> => fetchServerApi(`/api/v1/repos/${id}`, { cache: "no-store" }),
  getPrs: (repoId: string): Promise<any[]> => fetchServerApi(`/api/v1/repos/${repoId}/prs`, { cache: "no-store" }),
  getLargeObjects: (): Promise<any[]> => fetchServerApi(`/api/v1/drive`, { cache: "no-store" }),
  getPrediction: (prId: string): Promise<any> => fetchServerApi(`/api/v1/prediction/${prId}`, { cache: "no-store" }),
  getJobs: (): Promise<any[]> => fetchServerApi("/api/v1/jobs", { cache: "no-store" }),
  generateReadme: (repoPath: string): Promise<any> => fetchServerApi("/api/v1/readme/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath }),
  })
};
