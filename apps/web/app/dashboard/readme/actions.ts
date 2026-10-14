"use server";

import { fetchServerApi } from "@/lib/server-api-client";

export async function getConnectedReposAction() {
  try {
    return await fetchServerApi("/api/v1/repos");
  } catch {
    return [];
  }
}

export async function generateReadmeAction(
  repoPath: string,
  repositoryId?: string,
  detailLevel: string = "detailed"
) {
  return fetchServerApi("/api/v1/readme/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_path: repoPath,
      repository_id: repositoryId || null,
      detail_level: detailLevel,
    }),
  });
}

export async function regenerateSectionAction(
  repoPath: string,
  sectionId: string,
  currentDraft: string,
  detailLevel: string = "detailed"
) {
  return fetchServerApi("/api/v1/readme/regenerate-section", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_path: repoPath,
      section_id: sectionId,
      current_draft: currentDraft,
      detail_level: detailLevel,
    }),
  });
}

export async function validateReadmeAction(
  draft: string,
  evidence: unknown,
  detailLevel: string = "detailed",
  sections?: Record<string, string>
) {
  return fetchServerApi("/api/v1/readme/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      draft,
      evidence,
      detail_level: detailLevel,
      sections: sections || {},
    }),
  });
}

export async function saveReadmeAction(
  repoPath: string,
  content: string,
  repositoryId?: string,
  status: string = "draft"
) {
  return fetchServerApi("/api/v1/readme/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_path: repoPath,
      content,
      repository_id: repositoryId || null,
      status,
    }),
  });
}

export async function approveReadmeAction(
  repoPath: string,
  content: string,
  repositoryId?: string
) {
  return fetchServerApi("/api/v1/readme/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_path: repoPath,
      content,
      repository_id: repositoryId || null,
    }),
  });
}
