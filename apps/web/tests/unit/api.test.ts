import { afterEach, describe, expect, it, vi } from "vitest";

import { describeFetchError, fetchHealth, serverApiBaseUrl } from "@/lib/api";
import type { HealthResponse } from "@/types";

const REPORT: HealthResponse = {
  status: "ok",
  service: "gitsync-studio-api",
  version: "0.1.0",
  environment: "test",
  timestamp: "2026-01-01T00:00:00Z",
  checks: {
    database: { status: "ok", latency_ms: 2, version: "16.4", detail: null, required: true },
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("serverApiBaseUrl", () => {
  it("prefers the in-network URL over the browser one", () => {
    vi.stubEnv("API_INTERNAL_BASE_URL", "http://api:8000");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000");

    expect(serverApiBaseUrl()).toBe("http://api:8000");
  });
});

describe("fetchHealth", () => {
  it("returns the parsed report on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(REPORT)));

    const snapshot = await fetchHealth();

    expect(snapshot).toEqual({ reachable: true, httpStatus: 200, report: REPORT });
  });

  it("treats a 503 as a valid report, not a transport failure", async () => {
    const downReport: HealthResponse = { ...REPORT, status: "error" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(downReport, 503)));

    const snapshot = await fetchHealth();

    expect(snapshot.reachable).toBe(true);
    if (snapshot.reachable) {
      expect(snapshot.httpStatus).toBe(503);
      expect(snapshot.report.status).toBe("error");
    }
  });

  it("reports any other error status as unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("nope", { status: 502 })));

    const snapshot = await fetchHealth();

    expect(snapshot.reachable).toBe(false);
    if (!snapshot.reachable) {
      expect(snapshot.error).toContain("502");
    }
  });

  it("never throws when the connection is refused", async () => {
    const failure = new TypeError("fetch failed", { cause: { code: "ECONNREFUSED" } });
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(failure));

    const snapshot = await fetchHealth();

    expect(snapshot.reachable).toBe(false);
    if (!snapshot.reachable) {
      expect(snapshot.error).toMatch(/api service/i);
    }
  });

  it("asks fetch for uncached data", async () => {
    const spy = vi.fn().mockResolvedValue(jsonResponse(REPORT));
    vi.stubGlobal("fetch", spy);

    await fetchHealth();

    const init = spy.mock.calls[0]?.[1] as RequestInit;
    expect(init.cache).toBe("no-store");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });
});

describe("describeFetchError", () => {
  it("names a timeout in plain language", () => {
    const timeout = new DOMException("The operation timed out.", "TimeoutError");

    expect(describeFetchError(timeout)).toMatch(/did not respond in time/i);
  });

  it("explains DNS failures", () => {
    const failure = new TypeError("fetch failed", { cause: { code: "ENOTFOUND" } });

    expect(describeFetchError(failure)).toMatch(/hostname/i);
  });

  it("falls back to a generic message for a non-error throw", () => {
    expect(describeFetchError("oops")).toMatch(/unknown error/i);
  });
});
