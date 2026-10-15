"""GitSync Studio API application factory.

Wiring only: configuration, logging, middleware, lifespan-managed resources and
router registration. Feature modules (``auth``, ``github``, ``prediction``,
``drive``, ``readme``) register their own routers as their phase lands.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.core.redis import create_redis_client
from app.db.session import create_db_engine, create_session_factory
from app.drive.router import router as drive_router
from app.github.router import router as github_router
from app.jobs.router import router as jobs_router
from app.ops.router import router as ops_router
from app.prediction.router import router as prediction_router
from app.readme.router import router as readme_router
from app.repos.router import router as repos_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create shared resources on startup, release them on shutdown.

    Connections are *not* opened eagerly: an unavailable database must show up
    as an unhealthy check, not as an API that refuses to boot.
    """
    settings = get_settings()

    engine = create_db_engine(settings)
    app.state.db_engine = engine
    app.state.db_session_factory = create_session_factory(engine)
    app.state.redis = create_redis_client(settings.redis_url)

    logger.info(
        "api.startup",
        environment=settings.app_env,
        version=settings.app_version,
        database=settings.sanitised_database_url,
    )
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await engine.dispose()
        logger.info("api.shutdown")


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="GitSync Studio API",
        version=settings.app_version,
        summary="Repository intelligence, Drive-backed large files, grounded README generation",
        docs_url=settings.docs_url,
        redoc_url=None,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # Added first, so it sits *inside* CORS: preflight responses skip the
    # access log, real responses still get a request id.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )

    v1 = APIRouter(prefix=settings.api_v1_prefix)
    v1.include_router(ops_router)
    v1.include_router(repos_router)
    v1.include_router(auth_router)
    v1.include_router(github_router)
    v1.include_router(drive_router)
    v1.include_router(prediction_router)
    v1.include_router(readme_router)
    v1.include_router(jobs_router)
    app.include_router(v1)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "health": f"{settings.api_v1_prefix}/health",
            "docs": settings.docs_url,
        }

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Never leak a stack trace to a client; the log keeps the detail."""
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "request.unhandled_exception",
            path=request.url.path,
            error=type(exc).__name__,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred.",
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id} if request_id else None,
        )

    return app


app = create_app()
