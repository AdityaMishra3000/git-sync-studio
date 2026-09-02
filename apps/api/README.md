# apps/api

FastAPI backend. One deployable application, divided into feature packages.

```bash
docker compose up api            # normal path
docker compose logs -f api
```

Outside Docker (PostgreSQL and Redis must be reachable at the `.env` addresses):

```bash
../../.venv/bin/uvicorn app.main:app --reload
```

## Layout

```text
app/main.py         application factory, lifespan, middleware, router mounting
app/core/           config, logging, middleware, dependency providers
app/db/             declarative base, async engine, session scope
app/ops/            health / readiness / liveness  (PHASE 0)
app/jobs/           Celery application and queue names
app/auth/           sessions, identity, RBAC                (PHASE 2, 7)
app/github/         App auth, REST/GraphQL, sync, webhooks  (PHASE 2)
app/prediction/     serving merge and timing predictions    (PHASE 3)
app/drive/          Drive-backed large objects, pointers    (PHASE 4)
app/readme/         evidence extraction and generation      (PHASE 5)
alembic/            migrations (first one lands in PHASE 1)
tests/              unit tests; tests/integration needs live services
```

The empty feature packages exist so the boundary is declared before anyone is
tempted to put GitHub code in `core`. A feature package may import `core` and
`db`; it must not reach into another feature package's internals.

## Conventions

- **Nothing reads `os.environ`.** Settings come from `app.core.config.Settings`,
  which validates them once at startup.
- **Probes report, they do not raise.** See `app/ops/service.py`: an unreachable
  dependency produces a described failure, never a 500.
- **Async all the way down.** `AsyncEngine`, `AsyncSession`, `redis.asyncio`. A
  blocking call inside a request handler stalls the event loop for everyone; if
  something must block, it goes through `anyio.to_thread.run_sync` or a task.
- **Resources live on `app.state`**, created in the lifespan handler and read
  through the dependencies in `app/core/dependencies.py`, so tests override in
  one place.

## Checks

```bash
../../.venv/bin/pytest                 # unit
RUN_INTEGRATION_TESTS=1 ../../.venv/bin/pytest -m integration
../../.venv/bin/mypy                   # strict, covers ../worker too
cd ../.. && .venv/bin/ruff check apps/api apps/worker
```

`mypy` runs in `--strict` mode and `ruff` enables the bandit (`S`) rules. Both are
enforced in CI, so a `# type: ignore` or a `# noqa` needs a comment saying why.
