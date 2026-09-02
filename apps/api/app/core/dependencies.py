"""FastAPI dependency providers.

Long-lived resources (engine, session factory, Redis client) are created once
in the lifespan handler and stored on ``app.state``. These helpers read them
back with real types, and give tests a single place to override.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.db.session import session_scope


def _from_state(request: Request, attribute: str) -> object:
    value = getattr(request.app.state, attribute, None)
    if value is None:
        raise RuntimeError(
            f"app.state.{attribute} is not initialised; the lifespan handler did not run"
        )
    return value


def get_db_engine(request: Request) -> AsyncEngine:
    """The process-wide async engine."""
    return cast(AsyncEngine, _from_state(request, "db_engine"))


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """The process-wide session factory."""
    return cast("async_sessionmaker[AsyncSession]", _from_state(request, "db_session_factory"))


def get_redis_client(request: Request) -> Redis:
    """The process-wide application Redis client."""
    return cast(Redis, _from_state(request, "redis"))


async def get_db_session(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[AsyncSession]:
    """Per-request database session."""
    async for session in session_scope(factory):
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
EngineDep = Annotated[AsyncEngine, Depends(get_db_engine)]
RedisDep = Annotated[Redis, Depends(get_redis_client)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
