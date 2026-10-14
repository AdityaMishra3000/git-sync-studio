
"use server";

import { fetchServerApi } from "@/lib/server-api-client";

export async function generateReadmeAction(repoPath: string) {
  return fetchServerApi("/api/v1/readme/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath }),
  });
}


export async function saveReadmeAction(repoPath: string, content: string) {
  return fetchServerApi("/api/v1/readme/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath, content }),
  });
}
