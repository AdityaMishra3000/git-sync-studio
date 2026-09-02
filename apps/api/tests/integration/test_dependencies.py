"""Integration tests against real PostgreSQL and Redis.

Skipped by default. Run them once ``docker compose up`` is healthy:

    cd apps/api
    RUN_INTEGRATION_TESTS=1 pytest -m integration

They are the automated half of the PHASE 0 Definition of Done - the API really
connects to PostgreSQL and Redis rather than to a stub.
"""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.redis import create_redis_client
from app.db.session import create_db_engine
from app.main import create_app, lifespan
from app.ops.service import probe_database, probe_redis

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 with PostgreSQL and Redis running",
    ),
]


async def test_postgres_is_reachable() -> None:
    settings = get_settings()
    engine = create_db_engine(settings)
    try:
        result = await probe_database(engine, timeout=5.0)
    finally:
        await engine.dispose()

    assert result.status == "ok", result.detail
    assert result.version is not None


async def test_redis_is_reachable() -> None:
    settings = get_settings()
    client = create_redis_client(settings.redis_url)
    try:
        result = await probe_redis(client, timeout=5.0)
    finally:
        await client.aclose()

    assert result.status == "ok", result.detail
    assert result.version is not None


async def test_health_endpoint_through_the_real_lifespan() -> None:
    """Boots the app for real: engine and Redis come from the lifespan handler."""
    app = create_app()

    async with (
        lifespan(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        response = await client.get("/api/v1/health")

    body = response.json()
    assert body["checks"]["database"]["status"] == "ok", body["checks"]["database"]
    assert body["checks"]["redis"]["status"] == "ok", body["checks"]["redis"]
    # `celery` may legitimately be down when no worker container is running, so
    # the service-level status is allowed to be "ok" or "degraded" - never "error".
    assert body["status"] in {"ok", "degraded"}
    assert response.status_code == 200
