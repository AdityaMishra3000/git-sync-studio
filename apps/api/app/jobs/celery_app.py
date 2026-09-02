"""Celery application factory.

Task *modules* are deliberately not imported here. This module is imported by
the API process to dispatch work by name (``send_task``) and by the worker
process to run it; only ``apps/worker/worker.py`` decides which task modules to
load. That keeps a broken task module from taking down the web API.

PHASE 6 fills in the real job set (repository sync, webhook processing, model
training, Drive transfers, README generation, Drive reconciliation).
"""

from __future__ import annotations

from datetime import timedelta

from celery import Celery

from app.core.config import get_settings

# Queue names are declared up front so later phases route work instead of
# piling every job onto one queue. A long Drive upload must not block webhooks.
QUEUE_DEFAULT = "default"
QUEUE_GITHUB = "github"
QUEUE_DRIVE = "drive"
QUEUE_ML = "ml"


def create_celery_app() -> Celery:
    """Build the configured Celery application."""
    settings = get_settings()

    celery_app = Celery(
        "gitsync_studio",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )

    celery_app.conf.update(
        # JSON only: pickle would let a compromised broker execute code.
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        # Report a task as started so job status is observable while it runs.
        task_track_started=True,
        # Acknowledge after completion so a killed worker's job is redelivered.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Long jobs (uploads, training) make prefetching actively harmful.
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=200,
        broker_connection_retry_on_startup=True,
        result_expires=timedelta(days=1),
        task_default_queue=QUEUE_DEFAULT,
    )

    return celery_app


celery_app = create_celery_app()
