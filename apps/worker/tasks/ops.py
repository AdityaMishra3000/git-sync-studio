"""Diagnostic tasks.

``ops.ping`` exists so the whole asynchronous path can be exercised end to end
without any business logic in the way: API -> Redis -> worker -> result backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Task

from app.jobs.celery_app import QUEUE_DEFAULT, celery_app


@celery_app.task(name="ops.ping", bind=True, queue=QUEUE_DEFAULT)
def ping(self: Task) -> dict[str, Any]:
    """Return identifying information about the worker that ran this task."""
    return {
        "status": "pong",
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "queue": self.request.delivery_info.get("routing_key")
        if self.request.delivery_info
        else None,
        "completed_at": datetime.now(UTC).isoformat(),
    }
