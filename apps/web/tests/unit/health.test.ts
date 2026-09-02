import { describe, expect, it } from "vitest";

import {
  describeCheck,
  formatLatency,
  impactOf,
  orderedChecks,
  STATUS_LABEL,
  statusTone,
} from "@/lib/health";
import type { ComponentHealth } from "@/types";

function health(overrides: Partial<ComponentHealth> = {}): ComponentHealth {
  return {
    status: "ok",
    latency_ms: 4.2,
    version: null,
    detail: null,
    required: true,
    ...overrides,
  };
}

describe("statusTone", () => {
  it("maps each API status onto exactly one tone", () => {
    expect(statusTone("ok")).toBe("positive");
    expect(statusTone("degraded")).toBe("caution");
    expect(statusTone("error")).toBe("negative");
  });

  it("labels every status, so colour is never the only signal", () => {
    expect(Object.values(STATUS_LABEL).every((label) => label.length > 0)).toBe(true);
  });
});

describe("orderedChecks", () => {
  it("puts the known dependencies in dependency order", () => {
    const ordered = orderedChecks({
      celery: health({ required: false }),
      redis: health(),
      database: health(),
    });

    expect(ordered.map((check) => check.name)).toEqual(["database", "redis", "celery"]);
  });

  it("appends unknown components alphabetically instead of dropping them", () => {
    const ordered = orderedChecks({
      zookeeper: health(),
      database: health(),
      drive: health(),
    });

    expect(ordered.map((check) => check.name)).toEqual(["database", "drive", "zookeeper"]);
  });

  it("returns nothing for an empty report", () => {
    expect(orderedChecks({})).toEqual([]);
  });
});

describe("formatLatency", () => {
  it("renders a dash when the probe reported no latency", () => {
    expect(formatLatency(null)).toBe("—");
  });

  it("collapses sub-millisecond timings", () => {
    expect(formatLatency(0.4)).toBe("<1 ms");
  });

  it("rounds to whole milliseconds", () => {
    expect(formatLatency(12.7)).toBe("13 ms");
  });
});

describe("describeCheck", () => {
  it("prefers the reported version when healthy", () => {
    const text = describeCheck({ name: "database", health: health({ version: "16.4" }) });

    expect(text).toBe("v16.4");
  });

  it("surfaces the failure detail verbatim", () => {
    const text = describeCheck({
      name: "redis",
      health: health({ status: "error", detail: "ConnectionError: refused" }),
    });

    expect(text).toBe("ConnectionError: refused");
  });

  it("says something useful when a failure carries no detail", () => {
    expect(
      describeCheck({ name: "celery", health: health({ status: "error", required: false }) }),
    ).toBe("Not running");
    expect(describeCheck({ name: "database", health: health({ status: "error" }) })).toBe(
      "Unavailable",
    );
  });
});

describe("impactOf", () => {
  it("mirrors the backend rule: required failures block, optional ones reduce", () => {
    expect(impactOf({ name: "database", health: health({ status: "error" }) })).toBe("blocking");
    expect(impactOf({ name: "celery", health: health({ status: "error", required: false }) })).toBe(
      "reduced",
    );
    expect(impactOf({ name: "redis", health: health() })).toBe("none");
  });
});
