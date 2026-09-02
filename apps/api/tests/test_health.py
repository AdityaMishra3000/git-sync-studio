"""Health endpoint behaviour.

These are the tests that guard the PHASE 0 Definition of Done: the contract is
that a required dependency going down produces a 503 with a machine-readable
report, and a missing Celery worker only degrades the service.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.middleware import REQUEST_ID_HEADER
from app.ops import router as ops_router
from app.ops.schemas import ComponentHealth


def _ok(version: str | None = None, *, required: bool = True) -> ComponentHealth:
    return ComponentHealth(status="ok", latency_ms=1.0, version=version, required=required)


def _down(*, required: bool = True) -> ComponentHealth:
    return ComponentHealth(status="error", latency_ms=1.0, detail="boom", required=required)


@pytest.fixture
def stub_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the three probes with healthy stubs; tests override selectively."""

    async def database(*_args: object, **_kwargs: object) -> ComponentHealth:
        return _ok("16.4")

    async def redis(*_args: object, **_kwargs: object) -> ComponentHealth:
        return _ok("7.4.1")

    async def celery(*_args: object, **_kwargs: object) -> ComponentHealth:
        return _ok(required=False)

    monkeypatch.setattr(ops_router, "probe_database", database)
    monkeypatch.setattr(ops_router, "probe_redis", redis)
    monkeypatch.setattr(ops_router, "probe_celery_workers", celery)


async def test_liveness_touches_no_dependency(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "gitsync-studio-api"
    assert body["version"]


async def test_health_reports_every_dependency(client: AsyncClient, stub_probes: None) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body["checks"]) == {"database", "redis", "celery"}
    assert body["checks"]["database"]["version"] == "16.4"
    assert body["environment"] == "test"
    assert body["timestamp"]


async def test_health_is_503_when_database_is_down(
    client: AsyncClient, stub_probes: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def database(*_args: object, **_kwargs: object) -> ComponentHealth:
        return _down()

    monkeypatch.setattr(ops_router, "probe_database", database)

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["checks"]["database"]["detail"] == "boom"


async def test_missing_worker_degrades_but_still_serves(
    client: AsyncClient, stub_probes: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def celery(*_args: object, **_kwargs: object) -> ComponentHealth:
        return _down(required=False)

    monkeypatch.setattr(ops_router, "probe_celery_workers", celery)

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


async def test_readiness_ignores_the_worker(
    client: AsyncClient, stub_probes: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def celery(*_args: object, **_kwargs: object) -> ComponentHealth:
        raise AssertionError("readiness must not probe Celery")

    monkeypatch.setattr(ops_router, "probe_celery_workers", celery)

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert set(response.json()["checks"]) == {"database", "redis"}


async def test_request_id_is_echoed_back(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live", headers={REQUEST_ID_HEADER: "trace-me-123"})

    assert response.headers[REQUEST_ID_HEADER] == "trace-me-123"


async def test_root_advertises_the_health_endpoint(client: AsyncClient) -> None:
    body = (await client.get("/")).json()

    assert body["health"] == "/api/v1/health"


async def test_openapi_is_served_under_the_versioned_prefix(
    client: AsyncClient, app: FastAPI
) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]
