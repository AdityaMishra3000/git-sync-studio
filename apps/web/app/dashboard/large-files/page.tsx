/* eslint-disable @typescript-eslint/no-explicit-any */

import { ApiService } from "@/lib/api-service";
import { LargeFilesClient } from "./large-files-client";

export default async function LargeFilesPage() {
  let objects: any[] = [];
  let driveStatus: any = null;
  let repos: any[] = [];

  try {
    const [objsRes, statusRes, reposRes] = await Promise.allSettled([
      ApiService.getLargeObjects(),
      ApiService.getDriveStatus(),
      ApiService.getRepos(),
    ]);

    if (objsRes.status === "fulfilled" && Array.isArray(objsRes.value)) {
      objects = objsRes.value;
    }
    if (statusRes.status === "fulfilled" && statusRes.value) {
      driveStatus = statusRes.value;
    }
    if (reposRes.status === "fulfilled" && Array.isArray(reposRes.value)) {
      repos = reposRes.value;
    }
  } catch (err: any) {
    if (err?.digest?.startsWith("NEXT_REDIRECT")) throw err;
    console.error("Error loading large files page data:", err);
  }

  return (
    <LargeFilesClient
      initialObjects={objects}
      initialStatus={driveStatus}
      repos={repos}
    />
  );
}
