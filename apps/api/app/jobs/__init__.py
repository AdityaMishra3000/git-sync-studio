"""Asynchronous job infrastructure (Celery application and queue names).

Task implementations live in ``apps/worker/tasks/``; this package owns the
Celery configuration that both the API and the worker import.
"""

from app.jobs.celery_app import celery_app

__all__ = ["celery_app"]
