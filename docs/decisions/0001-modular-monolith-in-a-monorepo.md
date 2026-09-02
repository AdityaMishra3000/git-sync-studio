# 0001 - Modular monolith in a monorepo, with one Python codebase for API and worker

- **Status:** accepted
- **Date:** 2026-09-03
- **Phase:** 0

## Context

GitSync Studio ships three features that look independent and are not:

- pull request merge prediction, over data ingested from GitHub
- Drive-backed large-file storage, keyed to a repository
- README generation, from evidence extracted from that same repository

They share `users`, `repositories`, and the GitHub adapter. Almost every read
crosses two of these concerns ("show me this repository's open PRs, their
predictions and its large objects"). Some operations are slow enough that they
cannot run inside an HTTP request: historical PR backfill, model training,
uploading a 500 MiB file to Drive, generating a README.

The team is four students working for eight weeks, part-time, and the work has to
be individually attributable in git history.

## Decision

**One FastAPI application** (`apps/api`), internally divided into feature
packages (`auth`, `github`, `prediction`, `drive`, `readme`) that depend on
`core` and `db` but not on each other's internals.

**One Celery worker process** (`apps/worker`) that imports the same `app`
package. It is a separate process and container, not a separate codebase: the
entrypoint and the task modules live in `apps/worker`, everything they call lives
in `apps/api/app`.

**One repository** holding the backend, the frontend, the shared TypeScript
contract, ML code, the CLI and infrastructure, with `docker compose` as the only
supported way to run the whole thing locally.

**Not** microservices, **not** Kubernetes, **not** a separate service per feature.

## Consequences

Good:

- A cross-feature read is a SQL join, not a distributed query.
- A schema change and the code that depends on it land in one reviewable commit.
- Heavy jobs still cannot block HTTP, because the worker is its own process.
- A new contributor runs `docker compose up` and has the whole system.
- One dependency set to pin, one lint configuration, one type checker run.

Bad, and accepted:

- API and worker scale together in terms of _code_: a change to shared code
  redeploys both. At this size that is a feature, not a cost.
- Package boundaries are enforced by review, not by the compiler. Nothing stops
  someone importing `app.drive.service` from `app.readme`; review has to catch it.
- The monorepo makes the CI graph coarser - a backend-only change still runs the
  frontend job. Acceptable for a project this size; path filters can come later.

Reversal cost: moving a feature package out to its own service later means giving
it its own database boundary and an API. The package boundaries above are exactly
what makes that possible without a rewrite, which is the point of drawing them
now instead of after the fact.

## Alternatives rejected

**Microservices per feature.** Three services, three deployments, three sets of
credentials, and a distributed join for the main dashboard read - to solve a
scaling problem this project does not have.

**Separate repositories.** The frontend needs the API's response shapes and the
worker needs the API's models. Two repositories would mean publishing a package
or copying types, and would make the git history of a single feature span two
review queues.

**Worker with its own copy of the domain code.** Guaranteed drift. The first time
a model gained a column and only one side learned about it, the job would fail in
production, not in CI.
