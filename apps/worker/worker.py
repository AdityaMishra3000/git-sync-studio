"""Celery worker entrypoint.

Run with::

    celery -A worker worker --loglevel=info --queues=default

The worker shares the API's codebase (``apps/api/app``) on purpose: this is a
modular monolith, so a job and the HTTP handler that queued it use the same
models, settings and adapters. Only the *entrypoint* is separate, because the
worker is deployed and scaled independently.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.jobs.celery_app import celery_app

_settings = get_settings()
configure_logging(_settings.log_level, _settings.log_format)

# Importing the task modules is what registers tasks with the Celery app.
# A new task module MUST be imported here or the worker will never see it.
from tasks import ops  # noqa: E402

__all__ = ["celery_app", "ops"]
