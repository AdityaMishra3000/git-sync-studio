/**
 * Operational contract, mirroring `apps/api/app/ops/schemas.py`.
 *
 * Field names are snake_case because they come straight off the wire from
 * FastAPI. Renaming them here would hide the fact that the API is the source
 * of truth.
 */

/** Health of one dependency, or of the service as a whole. */
export type ComponentStatus = "ok" | "degraded" | "error";

export interface ComponentHealth {
  status: ComponentStatus;
  /** Round-trip time of the probe, in milliseconds. */
  latency_ms: number | null;
  /** Version reported by the dependency, when it exposes one. */
  version: string | null;
  /** Human-readable note; carries the error message on failure. */
  detail: string | null;
  /** When false, a failure degrades the service instead of breaking it. */
  required: boolean;
}

export interface HealthResponse {
  status: ComponentStatus;
  service: string;
  version: string;
  environment: string;
  /** ISO-8601 timestamp. */
  timestamp: string;
  checks: Record<string, ComponentHealth>;
}

export interface LivenessResponse {
  status: "ok";
  service: string;
  version: string;
}

/** Shape returned by the API's unhandled-exception handler. */
export interface ApiError {
  error: string;
  detail: string;
  request_id: string | null;
}
