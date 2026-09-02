# GitSync Studio

Repository intelligence and collaboration assistant. It reads a repository's own
history and tells you what that history actually says: which pull requests are
likely to land and when, where the large binaries went, and what a README can
honestly claim.

Three capabilities, one application:

| Capability                       | What it answers                                                                      | Phase |
| -------------------------------- | ------------------------------------------------------------------------------------ | ----- |
| **Pull request merge predictor** | Merge probability, expected time bucket, confidence, and the reasons - advisory only | 3     |
| **Drive-backed large files**     | SHA-256 addressed objects in Google Drive; Git carries a pointer, not 500 MiB        | 4     |
| **Grounded README generator**    | A draft where every claim traces to repository evidence, behind human approval       | 5     |

> **Status: PHASE 0 complete.** The platform boots, all five services are healthy,
> and the API reports on every dependency it has. No product feature is
> implemented yet - that is deliberate. See [docs/roadmap.md](docs/roadmap.md).

## Quick start

Requires Docker with the Compose plugin, Node 20.9+, and Python 3.12+.

```bash
./scripts/dev/bootstrap.sh      # creates .env, .venv, installs npm workspaces
docker compose up --build       # web, api, worker, postgres, redis
./scripts/dev/verify-phase-0.sh # asserts every PHASE 0 requirement
```

Then:

- <http://localhost:3100> - the web app
- <http://localhost:3100/dashboard> - live platform status
- <http://localhost:8000/api/v1/health> - the machine-readable version of it
- <http://localhost:8000/docs> - interactive API documentation

`make` lists the everyday commands.

## What is running

```text
Browser -> web (Next.js :3100) -> api (FastAPI :8000) -> postgres (:5433)
                                       |                 redis    (:6380)
                                       +-- enqueue --> worker (Celery)
```

Host ports avoid 3000 and 5432 because those are usually already taken, and
everything is bound to `127.0.0.1` so a development database is never exposed to
the network. Change the ports in `.env`.

`/api/v1/health` probes all three dependencies concurrently and distinguishes
required from optional: PostgreSQL or Redis down means HTTP 503 and `error`, a
missing Celery worker means HTTP 200 and `degraded`, because the API still serves
requests without one.

## Layout

```text
apps/api                FastAPI backend - a modular monolith, one package per feature
apps/worker             Celery entrypoint and task modules (shares apps/api's code)
apps/web                Next.js App Router frontend
packages/shared-types   TypeScript view of the API contract
ml/                     offline model training                       (PHASE 3)
cli/                    the `gitsync` command-line client            (PHASE 4)
repo-analysis/          deterministic repository evidence extraction (PHASE 5)
infra/docker            Dockerfiles (dev and production targets)
scripts/dev             bootstrap and Definition-of-Done verification
docs/                   architecture, roadmap, API, decisions
```

Directories for later phases hold a README describing what lands there and when.
Empty directory trees are not created in advance - they look like progress without
being any.

## Stack

Next.js · React · TypeScript · Tailwind CSS · shadcn/ui — FastAPI · Pydantic ·
SQLAlchemy 2 · Alembic — PostgreSQL — Redis · Celery — scikit-learn, pandas, NumPy
(PHASE 3) — Typer (PHASE 4) — Docker · Docker Compose · GitHub Actions —
pytest · Vitest · Playwright.

This list is fixed. Adding to it requires a concrete requirement and a decision
record; swapping PostgreSQL or FastAPI out is not on the table.

## Tests

```bash
make test        # pytest unit tests + vitest unit/component tests
make test-int    # pytest -m integration, against real PostgreSQL and Redis
make test-e2e    # Playwright, against the running stack
make lint typecheck
```

`mypy --strict` covers the backend including the worker; `ruff` runs with the
bandit security rules enabled; the frontend runs ESLint, `tsc` and Prettier. CI
runs all of it plus `scripts/dev/verify-phase-0.sh` against a real
`docker compose` stack on every pull request.

## Contributing

Issue, feature branch, tests, pull request, review, merge. Conventional commits.
Nothing goes directly to `main`. Details in [CONTRIBUTING.md](CONTRIBUTING.md);
the constraints the project will not relax are in [CLAUDE.md](CLAUDE.md) and
[docs/roadmap.md](docs/roadmap.md).

## Documentation

- [docs/development.md](docs/development.md) - running it, ports, troubleshooting
- [docs/roadmap.md](docs/roadmap.md) - the phases and their Definitions of Done
- [docs/architecture/overview.md](docs/architecture/overview.md) - topology and module boundaries
- [docs/api/README.md](docs/api/README.md) - endpoint inventory
- [docs/decisions/](docs/decisions/) - architecture decision records

## License

MIT. See [LICENSE](LICENSE).
