"""Operational endpoints: liveness, readiness and full health.

Three endpoints because they answer three different questions:

* ``/health/live``  - is the process up? (container restart decisions)
* ``/health/ready`` - can it serve traffic? (load-balancer decisions)
* ``/health``       - what is the state of everything? (humans, CI, PHASE 0 proof)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Response, status

from app.core.dependencies import EngineDep, RedisDep, SettingsDep
from app.ops.schemas import ComponentHealth, HealthResponse, LivenessResponse
from app.ops.service import (
    aggregate_status,
    probe_celery_workers,
    probe_database,
    probe_redis,
)

router = APIRouter(tags=["ops"])


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
)
async def liveness(settings: SettingsDep) -> LivenessResponse:
    """Always 200 while the process can serve requests. Touches no dependency."""
    return LivenessResponse(service=settings.app_name, version=settings.app_version)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Full health report",
    responses={503: {"model": HealthResponse, "description": "A required dependency is down"}},
)
async def health(
    settings: SettingsDep,
    engine: EngineDep,
    redis: RedisDep,
    response: Response,
) -> HealthResponse:
    """Probe PostgreSQL, Redis and the Celery workers concurrently.

    Returns 503 when PostgreSQL or Redis is unreachable. A missing Celery worker
    reports ``degraded`` with a 200, because the API still serves requests.
    """
    timeout = settings.health_check_timeout
    database, cache, workers = await asyncio.gather(
        probe_database(engine, timeout),
        probe_redis(redis, timeout),
        probe_celery_workers(timeout),
    )
    checks: dict[str, ComponentHealth] = {
        "database": database,
        "redis": cache,
        "celery": workers,
    }
    overall = aggregate_status(checks)
    if overall == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
        checks=checks,
    )


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    responses={503: {"model": HealthResponse, "description": "Not ready to serve traffic"}},
)
async def readiness(
    settings: SettingsDep,
    engine: EngineDep,
    redis: RedisDep,
    response: Response,
) -> HealthResponse:
    """Readiness depends only on the stores the request path needs."""
    timeout = settings.health_check_timeout
    database, cache = await asyncio.gather(
        probe_database(engine, timeout),
        probe_redis(redis, timeout),
    )
    checks: dict[str, ComponentHealth] = {"database": database, "redis": cache}
    overall = aggregate_status(checks)
    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
        checks=checks,
    )
