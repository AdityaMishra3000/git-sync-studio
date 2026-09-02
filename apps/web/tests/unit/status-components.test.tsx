import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "@/components/status-badge";
import { SystemStatus } from "@/components/system-status";
import type { HealthSnapshot } from "@/lib/api";
import type { ComponentHealth, HealthResponse } from "@/types";

function health(overrides: Partial<ComponentHealth> = {}): ComponentHealth {
  return {
    status: "ok",
    latency_ms: 3,
    version: null,
    detail: null,
    required: true,
    ...overrides,
  };
}

function report(overrides: Partial<HealthResponse> = {}): HealthResponse {
  return {
    status: "ok",
    service: "gitsync-studio-api",
    version: "0.1.0",
    environment: "development",
    timestamp: "2026-01-01T00:00:00Z",
    checks: {
      database: health({ version: "16.4" }),
      redis: health({ version: "7.4.1" }),
      celery: health({ required: false, detail: "1 worker(s) online: celery@w1" }),
    },
    ...overrides,
  };
}

describe("StatusBadge", () => {
  it("always renders a text label, so meaning is never carried by colour alone", () => {
    render(<StatusBadge status="degraded" />);

    expect(screen.getByText("Degraded")).toBeInTheDocument();
  });

  it("uses a distinct label per status", () => {
    const { rerender } = render(<StatusBadge status="ok" />);
    expect(screen.getByText("Operational")).toBeInTheDocument();

    rerender(<StatusBadge status="error" />);
    expect(screen.getByText("Down")).toBeInTheDocument();
  });
});

describe("SystemStatus", () => {
  it("names every dependency and its latency", () => {
    const snapshot: HealthSnapshot = { reachable: true, httpStatus: 200, report: report() };

    render(<SystemStatus snapshot={snapshot} />);

    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    expect(screen.getByText("Redis")).toBeInTheDocument();
    expect(screen.getByText("Celery worker")).toBeInTheDocument();
    expect(screen.getAllByText("3 ms")).toHaveLength(3);
  });

  it("explains that a missing worker is not fatal", () => {
    const snapshot: HealthSnapshot = {
      reachable: true,
      httpStatus: 200,
      report: report({
        status: "degraded",
        checks: {
          database: health({ version: "16.4" }),
          redis: health({ version: "7.4.1" }),
          celery: health({ status: "error", required: false }),
        },
      }),
    };

    render(<SystemStatus snapshot={snapshot} />);

    expect(screen.getByText(/keeps serving requests without it/i)).toBeInTheDocument();
  });

  it("tells the reader how to fix an unreachable backend", () => {
    const snapshot: HealthSnapshot = { reachable: false, error: "Nothing is listening." };

    render(<SystemStatus snapshot={snapshot} />);

    expect(screen.getByText("Backend unreachable")).toBeInTheDocument();
    expect(screen.getByText(/docker compose up/)).toBeInTheDocument();
  });
});
