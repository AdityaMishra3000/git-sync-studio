# CLAUDE.md

Working agreement for anyone - human or agent - changing this repository.

## What this project is

GitSync Studio: a **modular monolith with asynchronous workers**, delivering three
capabilities - pull request merge prediction, Git-LFS-inspired Google Drive backed
large-file storage, and grounded README generation.

Read [docs/roadmap.md](docs/roadmap.md) before starting anything. Work belongs to a
phase; phases land in order.

## Build one phase at a time

The current phase is the only phase. Do not implement, scaffold, or "prepare for"
a later one. Before moving on:

1. `make lint typecheck test` passes.
2. The phase's Definition of Done script passes (`scripts/dev/verify-phase-0.sh`
   for PHASE 0; later phases add their own).
3. Documentation reflects what now runs.
4. The work is committed in reviewable commits and merged through a PR.
5. Report what was implemented, what technical debt was added, and what remains.

**PHASE 0 is complete.** PHASE 1 is next: `users` and `repositories` tables,
`GET/POST /api/v1/repos`, and a dashboard that lists repositories from the
database.

## Fixed stack

Next.js · React · TypeScript · Tailwind CSS · shadcn/ui — FastAPI · Pydantic ·
SQLAlchemy 2 · Alembic — PostgreSQL — Redis · Celery — NumPy · pandas ·
scikit-learn · joblib — GitHub App (REST, GraphQL, webhooks) — Google OAuth 2.0 ·
Drive API — Typer — Docker · Docker Compose · GitHub Actions · GHCR —
pytest · Vitest · Playwright.

Adding a technology requires a concrete requirement it satisfies and a decision
record. Replacing one of the above is out of scope.

## Do not

- Build microservices, or introduce Kubernetes.
- Implement the Git LFS transfer protocol. This is LFS-_inspired_ pointer storage.
- Start the predictor with deep learning. Logistic regression, then trees.
- Use a random train/test split. Temporal splits only - a random split leaks
  future repository behaviour into training.
- Let a prediction reject a pull request or rank a contributor. Advisory only.
- Let the README generator state anything the evidence does not support, or write
  a README without human approval.
- Put a secret in source, a public Drive link on private data, or a refresh token
  in a browser.
- Trust an unsigned webhook.
- Create abstractions before there are two call sites, or directory trees before
  there is code to put in them.
- Skip tests to move faster, commit straight to `main`, or squash a phase into one
  commit.

## Conventions that already exist - match them

**Backend.** Nothing reads `os.environ`; settings come from
`app.core.config.Settings`. Probes and adapters _report_ failure rather than
raising - see `app/ops/service.py`. Shared resources are created in the lifespan
handler, stored on `app.state`, and read through `app/core/dependencies.py`. Async
throughout; anything blocking goes through `anyio.to_thread.run_sync` or a Celery
task. `mypy --strict` and `ruff` (with bandit rules) both pass, including for
`apps/worker`.

**Feature packages** (`app/auth`, `app/github`, `app/prediction`, `app/drive`,
`app/readme`) may import `app/core` and `app/db`. They must not import each
other's internals.

**Celery.** Task modules live in `apps/worker/tasks/` and must be imported in
`apps/worker/worker.py`, or Celery never sees them. Arguments must be JSON
serialisable: pass ids, not ORM objects. The API dispatches by name with
`celery_app.send_task`.

**Frontend.** Server components fetch; a client component needs an interaction to
justify it. `lib/api.ts` never throws - failures come back as data. Only
`NEXT_PUBLIC_*` reaches the browser. Types come from `@/types`, field names stay
`snake_case` because that is what the API sends. Colour is never the only signal:
status ships with an icon and a text label.

**Comments** explain why, not what. The code already says what.

## Commands

```bash
make                # list targets
make up             # docker compose up -d --build --wait
make verify         # PHASE 0 Definition of Done
make lint typecheck test
make test-int       # integration tests, stack must be up
make test-e2e       # Playwright, stack must be up
make migration m="add users"   # then read the generated migration
make migrate
```

Python tooling lives in `./.venv`. Do not install into the system interpreter.

## Ports

Web 3100, API 8000, PostgreSQL 5433, Redis 6380 - all on `127.0.0.1`. 3000 and
5432 are avoided because they are usually already in use. Override in `.env`.
