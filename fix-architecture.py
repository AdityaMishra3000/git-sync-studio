import os

web_path = "apps/web"

def read_file(path):
    with open(os.path.join(web_path, path), "r") as f:
        return f.read()

def write_file(path, content):
    full_path = os.path.join(web_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# 1. lib/api-client.ts (Browser safe)
write_file("lib/api-client.ts", """
import { browserApiBaseUrl } from "./api";

export async function fetchApi(path: string, options: RequestInit = {}) {
  const baseUrl = browserApiBaseUrl();
  const headers = new Headers(options.headers);

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
""")

# 2. lib/server-api-client.ts (Server safe)
write_file("lib/server-api-client.ts", """
import { serverApiBaseUrl } from "./api";
import { getToken } from "./auth";

export async function fetchServerApi(path: string, options: RequestInit = {}) {
  const token = await getToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${serverApiBaseUrl()}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
""")

# 3. lib/api-service.ts
api_service = read_file("lib/api-service.ts")
api_service = api_service.replace('import { fetchApi } from "./api-client";', 'import { fetchServerApi } from "./server-api-client";')
api_service = api_service.replace('fetchApi', 'fetchServerApi')
write_file("lib/api-service.ts", api_service)

# 4. app/dashboard/readme/actions.ts (Server action)
write_file("app/dashboard/readme/actions.ts", """
"use server";

import { fetchServerApi } from "@/lib/server-api-client";

export async function generateReadmeAction(repoPath: string) {
  return fetchServerApi("/api/v1/readme/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath }),
  });
}
""")

# 5. app/dashboard/readme/page.tsx (Client component)
readme_page = read_file("app/dashboard/readme/page.tsx")
readme_page = readme_page.replace('import { fetchApi } from "@/lib/api-client";', 'import { generateReadmeAction } from "./actions";')
readme_page = readme_page.replace("""      const data = await fetchApi("/api/v1/readme/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath }),
      });""", """      const data = await generateReadmeAction(repoPath);""")
write_file("app/dashboard/readme/page.tsx", readme_page)

# 6. app/dashboard/page.tsx (Fix 404 button)
dashboard_page = read_file("app/dashboard/page.tsx")
dashboard_page = dashboard_page.replace('href="/api/v1/auth/github/login"', 'href="/login"')
write_file("app/dashboard/page.tsx", dashboard_page)

print("Architecture fixed.")
