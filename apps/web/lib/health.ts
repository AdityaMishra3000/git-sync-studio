/**
 * Presentation helpers for health data. Pure functions, no React - so they can
 * be unit tested without a DOM.
 */

import type { ComponentHealth, ComponentStatus } from "@/types";

export type Tone = "positive" | "caution" | "negative";

export const STATUS_LABEL: Record<ComponentStatus, string> = {
  ok: "Operational",
  degraded: "Degraded",
  error: "Down",
};

export function statusTone(status: ComponentStatus): Tone {
  switch (status) {
    case "ok":
      return "positive";
    case "degraded":
      return "caution";
    case "error":
      return "negative";
  }
}

/** Components render in dependency order, then alphabetically, so the UI is stable. */
const PREFERRED_ORDER = ["database", "redis", "celery"];

export interface NamedCheck {
  name: string;
  health: ComponentHealth;
}

export function orderedChecks(checks: Record<string, ComponentHealth>): NamedCheck[] {
  const rank = (name: string): number => {
    const index = PREFERRED_ORDER.indexOf(name);
    return index === -1 ? PREFERRED_ORDER.length : index;
  };

  return Object.entries(checks)
    .map(([name, health]) => ({ name, health }))
    .sort((a, b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name));
}

export function formatLatency(latencyMs: number | null): string {
  if (latencyMs === null || Number.isNaN(latencyMs)) return "—";
  if (latencyMs < 1) return "<1 ms";
  return `${Math.round(latencyMs)} ms`;
}

/** Short human sentence for one component, used under its name. */
export function describeCheck(check: NamedCheck): string {
  const { health } = check;
  if (health.status === "ok") {
    return health.version ? `v${health.version}` : (health.detail ?? "Connected");
  }
  if (health.detail) return health.detail;
  return health.required ? "Unavailable" : "Not running";
}

/**
 * Whether a failing component blocks the product or merely reduces it.
 * Mirrors the API's aggregation rule so the UI never contradicts the backend.
 */
export function impactOf(check: NamedCheck): "blocking" | "reduced" | "none" {
  if (check.health.status === "ok") return "none";
  return check.health.required ? "blocking" : "reduced";
}
