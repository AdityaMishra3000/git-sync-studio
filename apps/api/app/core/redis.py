"""Redis client lifecycle.

Redis has two distinct jobs in GitSync Studio: it is the Celery broker/result
backend (PHASE 6) and the application's cache / rate-limit store (PHASE 7).
This module owns the *application* client only; Celery manages its own
connections from ``app.jobs.celery_app``.
"""

from __future__ import annotations

from typing import cast

from redis.asyncio import Redis


def create_redis_client(url: str) -> Redis:
    """Build an application Redis client.

    ``decode_responses=True`` keeps call sites working with ``str`` instead of
    ``bytes``. Health checks and timeouts are bounded so a hung Redis surfaces
    as a failed check rather than a hung request.
    """
    # `Redis.from_url` is unannotated upstream, hence the cast.
    return cast(
        Redis,
        Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
            retry_on_timeout=True,
        ),
    )
