# Worker

Celery worker for GitSync Studio. Thin by design: the entrypoint and the task
modules live here, the logic they call lives in `apps/api/app`.

## Running

```bash
docker compose up worker            # normal path
docker compose logs -f worker
```

Locally, with `apps/api` deps installed and PostgreSQL/Redis reachable:

```bash
PYTHONPATH=../api celery -A worker worker --loglevel=info
```

## Why the code is shared with the API

GitSync Studio is a modular monolith. A job that syncs a repository needs the
same GitHub adapter, the same SQLAlchemy models and the same settings as the
HTTP handler that enqueued it. Duplicating them would guarantee drift. The
worker is a separate _process and container_ so heavy jobs (Drive uploads, model
training) cannot block HTTP requests - not a separate codebase.

## Adding a task

1. Put it in `tasks/<domain>.py` and decorate with `@celery_app.task(name="domain.action")`.
2. Import the module in `worker.py` - unimported modules are invisible to Celery.
3. Enqueue it from the API with `celery_app.send_task("domain.action", ...)`.
4. Route long jobs onto their own queue (`QUEUE_GITHUB`, `QUEUE_DRIVE`, `QUEUE_ML`).

Task arguments must be JSON-serialisable: pass ids, not ORM objects.

## Queues

| Queue     | Carries                             | Phase |
| --------- | ----------------------------------- | ----- |
| `default` | diagnostics, small bookkeeping jobs | 0     |
| `github`  | repository sync, webhook processing | 2     |
| `ml`      | dataset build, model training       | 3     |
| `drive`   | large-file transfer, reconciliation | 4     |
