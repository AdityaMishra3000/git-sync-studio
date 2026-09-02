"""Dependency probes behind the health endpoints.

Each probe is bounded by a timeout and never raises: an unreachable dependency
must produce a *report*, not a 500. The aggregate rule is:

* a failing **required** dependency (PostgreSQL, Redis) -> ``error``
* a failing **optional** dependency (Celery workers)    -> ``degraded``

The API is still useful with no worker running, so worker absence must not take
the whole service out of rotation.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from anyio import to_thread
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.ops.schemas import ComponentHealth, ComponentStatus


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _failure(started: float, exc: BaseException, *, required: bool = True) -> ComponentHealth:
    if isinstance(exc, TimeoutError):
        detail = "probe timed out"
    else:
        detail = f"{type(exc).__name__}: {exc}".strip()
    return ComponentHealth(
        status="error",
        latency_ms=_elapsed_ms(started),
        detail=detail[:300],
        required=required,
    )


async def probe_database(engine: AsyncEngine, timeout: float) -> ComponentHealth:
    """Open a connection and run ``SELECT 1``, reporting the server version."""
    started = time.perf_counter()
    try:
        async with asyncio.timeout(timeout), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            raw_version = await connection.scalar(text("SHOW server_version"))
    except Exception as exc:  # noqa: BLE001 - a probe reports, it does not raise
        return _failure(started, exc)
    return ComponentHealth(
        status="ok",
        latency_ms=_elapsed_ms(started),
        version=str(raw_version) if raw_version else None,
        detail="connected",
    )


async def probe_redis(client: Redis, timeout: float) -> ComponentHealth:
    """PING Redis and report its version."""
    started = time.perf_counter()
    try:
        async with asyncio.timeout(timeout):
            await client.ping()
            info: dict[str, Any] = await client.info("server")
    except Exception as exc:  # noqa: BLE001
        return _failure(started, exc)
    return ComponentHealth(
        status="ok",
        latency_ms=_elapsed_ms(started),
        version=str(info.get("redis_version")) if info.get("redis_version") else None,
        detail="connected",
    )


async def probe_celery_workers(timeout: float) -> ComponentHealth:
    """Broadcast a control ping and report which workers answered.

    ``control.ping`` is blocking, so it runs in a worker thread. ``limit=1``
    makes it return as soon as one worker replies instead of always waiting the
    full timeout for stragglers - without it, a healthy stack still paid ~2s on
    every health request. With no worker running it does wait out the budget,
    which is why the budget is short.
    """
    from app.jobs.celery_app import celery_app

    started = time.perf_counter()
    budget = min(timeout, 1.0)
    try:
        replies = await to_thread.run_sync(lambda: celery_app.control.ping(timeout=budget, limit=1))
    except Exception as exc:  # noqa: BLE001
        return _failure(started, exc, required=False)

    names = [name for reply in (replies or []) for name in reply]
    if not names:
        return ComponentHealth(
            status="error",
            latency_ms=_elapsed_ms(started),
            detail="no Celery worker answered the control ping",
            required=False,
        )
    return ComponentHealth(
        status="ok",
        latency_ms=_elapsed_ms(started),
        detail=f"{len(names)} worker(s) online: {', '.join(sorted(names))}"[:300],
        required=False,
    )


def aggregate_status(checks: dict[str, ComponentHealth]) -> ComponentStatus:
    """Fold component results into one service-level status."""
    if any(check.status == "error" and check.required for check in checks.values()):
        return "error"
    if any(check.status != "ok" for check in checks.values()):
        return "degraded"
    return "ok"
