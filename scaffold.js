const fs = require('fs');
const path = require('path');

const webPath = path.join(__dirname, 'apps/web');

// 1. Types
const typesCode = `
export type Repository = {
  id: string;
  owner: string;
  name: string;
  github_repo_id: number;
  default_branch: string;
  visibility: string;
  sync_status: string;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  email: string;
  name: string | null;
};
`;
fs.writeFileSync(path.join(webPath, 'types/models.ts'), typesCode);

// 2. Auth Utils
const authCode = `
import { cookies } from "next/headers";

export async function getToken() {
  return cookies().get("gitsync_token")?.value;
}

export async function setToken(token: string) {
  cookies().set("gitsync_token", token, { path: "/", httpOnly: true });
}

export async function clearToken() {
  cookies().delete("gitsync_token");
}
`;
fs.writeFileSync(path.join(webPath, 'lib/auth.ts'), authCode);

// 3. API Client Wrapper
const apiClientCode = `
import { serverApiBaseUrl, browserApiBaseUrl } from "./api";
import { getToken } from "./auth";

export async function fetchApi(path: string, options: RequestInit = {}) {
  const isServer = typeof window === "undefined";
  const baseUrl = isServer ? serverApiBaseUrl() : browserApiBaseUrl();
  const url = \`\${baseUrl}\${path}\`;
  
  const headers = new Headers(options.headers);
  if (isServer) {
    const token = await getToken();
    if (token) headers.set("Authorization", \`Bearer \${token}\`);
  } else {
    // In browser, we rely on a wrapper or cookie logic if exposed, 
    // but typically we'll do data fetching via Server Actions or Server Components.
  }

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    throw new Error(\`API Error: \${res.status} \${res.statusText}\`);
  }
  return res.json();
}
`;
fs.writeFileSync(path.join(webPath, 'lib/api-client.ts'), apiClientCode);

// 4. API Service
const apiServiceCode = `
import { fetchApi } from "./api-client";
import { Repository, User } from "../types/models";

export const ApiService = {
  getMe: (): Promise<User> => fetchApi("/api/v1/auth/me", { cache: "no-store" }),
  getLoginUrl: (): Promise<{ url: string }> => fetchApi("/api/v1/auth/github/login", { cache: "no-store" }),
  getRepos: (): Promise<Repository[]> => fetchApi("/api/v1/repos", { cache: "no-store" }),
  getRepo: (id: string): Promise<Repository> => fetchApi(\`/api/v1/repos/\${id}\`, { cache: "no-store" }),
  getPrediction: (prId: string): Promise<any> => fetchApi(\`/api/v1/prediction/\${prId}\`, { cache: "no-store" }),
  generateReadme: (repoPath: string): Promise<any> => fetchApi("/api/v1/readme/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath }),
  })
};
`;
fs.writeFileSync(path.join(webPath, 'lib/api-service.ts'), apiServiceCode);

console.log("Scaffold complete.");
