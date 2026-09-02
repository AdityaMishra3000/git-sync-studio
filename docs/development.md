# Development

## First run

```bash
./scripts/dev/bootstrap.sh     # .env, .venv, npm workspaces
docker compose up --build      # web, api, worker, postgres, redis
./scripts/dev/verify-phase-0.sh
```

`make` lists everything else:

```bash
make            # help
make up         # docker compose up -d --build --wait
make verify     # assert the PHASE 0 Definition of Done
make lint typecheck test
```

## Addresses

| Service    | URL / DSN                                     | Notes                              |
| ---------- | --------------------------------------------- | ---------------------------------- |
| Web        | http://localhost:3100                         | `WEB_HOST_PORT`                    |
| API        | http://localhost:8000                         | `API_HOST_PORT`                    |
| API docs   | http://localhost:8000/docs                    | disabled when `APP_ENV=production` |
| Health     | http://localhost:8000/api/v1/health           | the PHASE 0 proof                  |
| PostgreSQL | `postgresql://gitsync@localhost:5433/gitsync` | `POSTGRES_HOST_PORT`               |
| Redis      | `redis://localhost:6380`                      | `REDIS_HOST_PORT`                  |

Ports 3000 and 5432 are avoided because they are usually already taken by
something else on a development machine. Everything is bound to `127.0.0.1`, so
none of it is reachable from the local network.

## Two views of the same services

`.env` holds the **host** view: `DATABASE_URL` points at `localhost:5433`, which
is what `alembic`, `psql` and `pytest -m integration` need when you run them
outside Docker. `compose.yaml` overrides `DATABASE_URL`, `REDIS_URL` and the
Celery URLs for the `api` and `worker` containers so they use the in-network
names `postgres` and `redis`. Credentials live in one place; only the hostname
differs.

## Editing code

- **Backend** - `apps/api` and `apps/worker` are bind-mounted. uvicorn reloads
  on save. The Celery worker does not: run `make restart` after changing a task.
- **Frontend** - `apps/web` and `packages/` are bind-mounted; Next.js hot-reloads.
- **Dependencies** - after editing `pyproject.toml` or a `package.json`, rebuild:
  `docker compose up -d --build`.

## Migrations

There are no migrations yet; the first one arrives in PHASE 1 with `users` and
`repositories`.

```bash
make migration m="add users and repositories"   # autogenerate
make migrate                                    # alembic upgrade head
```

Always read a generated migration before committing it. Autogenerate misses
server defaults, enum changes and index renames.

## Tests

```bash
make test        # pytest (unit) + vitest
make test-int    # pytest -m integration, needs the stack up
make test-e2e    # Playwright, needs the stack up
```

`npm run test:e2e:install --workspace=web` downloads the browser once.

## Troubleshooting

**`docker compose up` fails on a port.** Something already owns it. Change
`WEB_HOST_PORT` / `API_HOST_PORT` / `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT` in
`.env`.

**The dashboard says "Backend unreachable".** The `api` container is down or
unhealthy: `docker compose ps`, then `docker compose logs api`.

**`/api/v1/health` returns 503.** Read the `checks` object - it names the
component and carries the error. PostgreSQL and Redis are required; a missing
Celery worker only produces `degraded` with a 200.

**The worker is not picking up tasks.** New task modules have to be imported in
`apps/worker/worker.py`; Celery cannot see a module nobody imported.

**Everything is odd after a dependency change.** `docker compose down -v` wipes
the volumes (including the database) and `docker compose up --build` rebuilds
from scratch.
