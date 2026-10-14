import { redirect } from "next/navigation";

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
    if (res.status === 401) {
      redirect("/login");
    }
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
