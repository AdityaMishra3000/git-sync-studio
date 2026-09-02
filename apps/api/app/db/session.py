"""Async SQLAlchemy engine and session plumbing.

The engine is created once during application startup and stored on
``app.state``; request handlers get a session through the ``get_db_session``
dependency. Nothing here imports models, so Alembic can use it too.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def create_db_engine(settings: Settings) -> AsyncEngine:
    """Build the async engine from settings."""
    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        # Detects connections killed by a database restart instead of handing a
        # dead connection to a request.
        pool_pre_ping=settings.db_pool_pre_ping,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build the session factory bound to ``engine``.

    ``expire_on_commit=False`` so objects stay usable after a commit, which
    avoids surprise lazy-loads while serialising a response.
    """
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a session, committing on success and rolling back on failure.

    Used by the FastAPI dependency and by Celery tasks, which have no request
    scope of their own.
    """
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
