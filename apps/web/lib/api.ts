/**
 * Typed access to the FastAPI backend.
 *
 * Two base URLs, deliberately:
 *
 * - `serverApiBaseUrl()` runs inside the container network (`http://api:8000`)
 *   and is used by server components, route handlers and server actions.
 * - `browserApiBaseUrl()` is what a browser can reach (`http://localhost:8000`).
 *
 * Only `NEXT_PUBLIC_*` values reach the browser bundle, so nothing secret may
 * ever be read here without the server-only guarantee of a server component.
 */

import type { HealthResponse } from "@/types";

const FALLBACK_BASE_URL = "http://localhost:8000";

export function serverApiBaseUrl(): string {
  return (
    process.env.API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? FALLBACK_BASE_URL
  );
}

export function browserApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? FALLBACK_BASE_URL;
}

/**
 * Result of asking the API how it is doing.
 *
 * `reachable: true` with an HTTP 503 is a normal outcome: the API answered and
 * told us a dependency is down. That is information, not a failure to fetch.
 */
export type HealthSnapshot =
  | { reachable: true; httpStatus: number; report: HealthResponse }
  | { reachable: false; error: string };

export function describeFetchError(error: unknown): string {
  if (error instanceof DOMException && error.name === "TimeoutError") {
    return "The API did not respond in time.";
  }
  if (error instanceof Error) {
    const cause = error.cause;
    if (cause && typeof cause === "object" && "code" in cause) {
      const code = String((cause as { code: unknown }).code);
      if (code === "ECONNREFUSED") {
        return "Nothing is listening on the API address. Is the api service running?";
      }
      if (code === "ENOTFOUND" || code === "EAI_AGAIN") {
        return "The API hostname could not be resolved.";
      }
      return `Network error: ${code}`;
    }
    return error.message;
  }
  return "Unknown error while contacting the API.";
}

/** Fetch the full health report. Never throws: failures come back as data. */
export async function fetchHealth(timeoutMs = 4000): Promise<HealthSnapshot> {
  const url = `${serverApiBaseUrl()}/api/v1/health`;

  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (!response.ok && response.status !== 503) {
      return {
        reachable: false,
        error: `The API answered ${response.status} ${response.statusText}.`,
      };
    }

    const report = (await response.json()) as HealthResponse;
    return { reachable: true, httpStatus: response.status, report };
  } catch (error) {
    return { reachable: false, error: describeFetchError(error) };
  }
}
