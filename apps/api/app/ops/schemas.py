"""Schemas for the operational (health / readiness) endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ComponentStatus = Literal["ok", "degraded", "error"]


class ComponentHealth(BaseModel):
    """Result of probing one dependency."""

    status: ComponentStatus
    latency_ms: float | None = Field(
        default=None, description="Round-trip time of the probe in milliseconds."
    )
    version: str | None = Field(
        default=None, description="Reported version of the dependency, when available."
    )
    detail: str | None = Field(
        default=None, description="Human-readable note; carries the error on failure."
    )
    required: bool = Field(
        default=True,
        description="If false, a failure degrades the service instead of breaking it.",
    )


class HealthResponse(BaseModel):
    """Aggregate health of the API and everything it depends on."""

    status: ComponentStatus
    service: str
    version: str
    environment: str
    timestamp: datetime
    checks: dict[str, ComponentHealth]


class LivenessResponse(BaseModel):
    """Process liveness. Deliberately checks nothing external."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
