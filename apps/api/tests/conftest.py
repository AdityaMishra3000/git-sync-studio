"""Shared pytest fixtures for the API test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest

# Pin the environment before anything under `app` is imported: several modules
# read settings at import time.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_FORMAT", "json")
os.environ.setdefault("SECRET_KEY", "test-only-secret")

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Keep the settings singleton from leaking between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def app() -> FastAPI:
    """An application instance with the lifespan resources stubbed out.

    ``ASGITransport`` does not run the lifespan handler, so ``app.state`` is
    populated here. Unit tests patch the probes instead of connecting anywhere.
    """
    application = create_app()
    application.state.db_engine = object()
    application.state.db_session_factory = object()
    application.state.redis = object()
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as http_client:
        yield http_client
