/**
 * The web app's type surface.
 *
 * Everything that crosses the API boundary is re-exported from here, so a
 * component imports `@/types` and never has to know whether a type is shared
 * with the backend or local to the UI. Browser-only view models get added
 * alongside these re-exports.
 */

export type {
  ApiError,
  ComponentHealth,
  ComponentStatus,
  HealthResponse,
  LivenessResponse,
} from "@gitsync/shared-types";
