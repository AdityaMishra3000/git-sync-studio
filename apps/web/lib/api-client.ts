
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
