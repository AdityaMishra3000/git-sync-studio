"""Unit tests for the dependency probes and the status aggregation rule."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.ops.schemas import ComponentHealth
from app.ops.service import (
    aggregate_status,
    probe_celery_workers,
    probe_database,
    probe_redis,
)


class _FakeConnection:
    def __init__(self, server_version: str) -> None:
        self._server_version = server_version

    async def execute(self, _statement: object) -> None:
        return None

    async def scalar(self, _statement: object) -> str:
        return self._server_version


class _FakeConnectionContext:
    def __init__(self, server_version: str, *, delay: float = 0.0) -> None:
        self._server_version = server_version
        self._delay = delay

    async def __aenter__(self) -> _FakeConnection:
        if self._delay:
            await asyncio.sleep(self._delay)
        return _FakeConnection(self._server_version)

    async def __aexit__(self, *_exc: object) -> None:
        return None


class _FakeEngine:
    def __init__(self, server_version: str = "16.4", *, delay: float = 0.0) -> None:
        self._server_version = server_version
        self._delay = delay

    def connect(self) -> _FakeConnectionContext:
        return _FakeConnectionContext(self._server_version, delay=self._delay)


class _BrokenEngine:
    def connect(self) -> _FakeConnectionContext:
        raise OSError("connection refused")


class _FakeRedis:
    def __init__(self, version: str = "7.4.1") -> None:
        self._version = version

    async def ping(self) -> bool:
        return True

    async def info(self, _section: str) -> dict[str, Any]:
        return {"redis_version": self._version}


class _BrokenRedis:
    async def ping(self) -> bool:
        raise ConnectionError("redis is not listening")


async def test_database_probe_reports_server_version() -> None:
    result = await probe_database(cast(AsyncEngine, _FakeEngine("16.4")), timeout=1.0)

    assert result.status == "ok"
    assert result.version == "16.4"
    assert result.latency_ms is not None


async def test_database_probe_turns_a_connection_error_into_a_report() -> None:
    result = await probe_database(cast(AsyncEngine, _BrokenEngine()), timeout=1.0)

    assert result.status == "error"
    assert result.detail is not None
    assert "connection refused" in result.detail


async def test_database_probe_honours_the_timeout() -> None:
    slow = _FakeEngine(delay=0.5)

    result = await probe_database(cast(AsyncEngine, slow), timeout=0.01)

    assert result.status == "error"
    assert result.detail == "probe timed out"


async def test_redis_probe_reports_version() -> None:
    result = await probe_redis(cast(Redis, _FakeRedis()), timeout=1.0)

    assert result.status == "ok"
    assert result.version == "7.4.1"


async def test_redis_probe_turns_a_connection_error_into_a_report() -> None:
    result = await probe_redis(cast(Redis, _BrokenRedis()), timeout=1.0)

    assert result.status == "error"
    assert result.required is True


class _FakeControl:
    def __init__(self, replies: list[dict[str, Any]] | None) -> None:
        self._replies = replies

    def ping(self, timeout: float = 1.0, limit: int | None = None) -> list[dict[str, Any]] | None:
        assert timeout > 0
        assert limit == 1, "the probe must stop at the first reply"
        return self._replies


@pytest.fixture
def patch_celery_control(monkeypatch: pytest.MonkeyPatch) -> Any:
    from app.jobs.celery_app import celery_app

    def _apply(replies: list[dict[str, Any]] | None) -> None:
        monkeypatch.setattr(celery_app, "control", _FakeControl(replies))

    return _apply


async def test_celery_probe_lists_online_workers(patch_celery_control: Any) -> None:
    patch_celery_control([{"celery@worker-1": {"ok": "pong"}}])

    result = await probe_celery_workers(timeout=1.0)

    assert result.status == "ok"
    assert result.detail is not None
    assert "celery@worker-1" in result.detail


async def test_celery_probe_flags_absence_as_optional_failure(
    patch_celery_control: Any,
) -> None:
    patch_celery_control([])

    result = await probe_celery_workers(timeout=1.0)

    assert result.status == "error"
    assert result.required is False


class _Case:
    """Named cases keep the aggregation table readable."""

    ok = ComponentHealth(status="ok")
    required_down = ComponentHealth(status="error", required=True)
    optional_down = ComponentHealth(status="error", required=False)
    degraded = ComponentHealth(status="degraded")


@pytest.mark.parametrize(
    ("checks", "expected"),
    [
        ({"db": _Case.ok, "redis": _Case.ok}, "ok"),
        ({"db": _Case.required_down, "redis": _Case.ok}, "error"),
        ({"db": _Case.ok, "celery": _Case.optional_down}, "degraded"),
        ({"db": _Case.ok, "redis": _Case.degraded}, "degraded"),
        ({"db": _Case.required_down, "celery": _Case.optional_down}, "error"),
        ({}, "ok"),
    ],
)
def test_aggregate_status(checks: dict[str, ComponentHealth], expected: str) -> None:
    assert aggregate_status(checks) == expected
