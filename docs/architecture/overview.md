# Architecture overview

## Runtime topology

```text
                    Browser
                       |
                       v
              +--------------------+
              |  web  (Next.js)    |   :3000  ->  host :3100
              |  server components |
              +--------------------+
                       |  http://api:8000
                       v
              +--------------------+        +------------------+
              |  api  (FastAPI)    |------->|  postgres :5432  |  host :5433
              |  modular monolith  |        +------------------+
              +--------------------+
                    |        |                +------------------+
                    |        +--------------->|  redis :6379     |  host :6380
                    |                         +------------------+
                    | enqueue (db 1)                  ^
                    v                                 |
              +--------------------+                  |
              | worker (Celery)    |------------------+
              +--------------------+   results (db 2)

  Redis db 0 = application cache, db 1 = Celery broker, db 2 = Celery results.
```

Later phases attach external services to `api` (GitHub App, REST, GraphQL,
webhooks; Google OAuth and Drive) and to the `gitsync` CLI, which talks to the
API rather than to Drive directly.

## Why a modular monolith

Three features share one domain: a pull request is the input to the predictor,
the repository is the input to the README generator, and both live next to the
large-object mapping. Splitting them into services would mean distributed
transactions and network hops for reads that a join answers. See
[decisions/0001](../decisions/0001-modular-monolith-in-a-monorepo.md).

Isolation comes from **package boundaries**, enforced by review:

| Package          | Owns                                           | Phase |
| ---------------- | ---------------------------------------------- | ----- |
| `app/core`       | config, logging, middleware, dependencies      | 0     |
| `app/db`         | declarative base, engine, sessions, models     | 0/1   |
| `app/ops`        | health, readiness, liveness                    | 0     |
| `app/jobs`       | Celery application and queue names             | 0     |
| `app/auth`       | sessions, identity, RBAC                       | 2/7   |
| `app/github`     | App auth, REST/GraphQL clients, sync, webhooks | 2     |
| `app/prediction` | serving merge/timing predictions               | 3     |
| `app/drive`      | Drive-backed large objects, pointers           | 4     |
| `app/readme`     | evidence extraction, generation, validation    | 5     |

A feature package may depend on `core` and `db`. It must not import another
feature package's internals; cross-feature work goes through a service function
that the owning package exports.

## Repository layout

Present today:

```text
apps/api              FastAPI application (the modular monolith)
apps/worker           Celery entrypoint and task modules
apps/web              Next.js App Router frontend
packages/shared-types TypeScript view of the API contract
infra/docker          Dockerfiles for the backend and web images
scripts/dev           bootstrap and Definition-of-Done verification
docs                  this directory
```

Reserved, created with the phase that fills them:

```text
ml/{datasets,features,training,evaluation,models,notebooks}   PHASE 3
cli/gitsync/{commands,filters,cache}                          PHASE 4
repo-analysis/{extractors,parsers,heuristics,readme}          PHASE 5
scripts/seed                                                  PHASE 1
```

Empty directory trees are not created ahead of time: a placeholder tree looks
like progress without being any, and it makes the real structure harder to read.

## Health model

`/api/v1/health` probes PostgreSQL, Redis and the Celery workers concurrently,
and each probe reports rather than raises. The aggregation rule is the whole
design:

- a failing **required** dependency (PostgreSQL, Redis) gives `error` and HTTP 503
- a failing **optional** dependency (Celery) gives `degraded` and HTTP 200

The API is useful without a worker - reads still serve - so worker absence must
not take the service out of rotation. `/health/live` touches nothing, so a
dependency outage never triggers a container restart loop. `/health/ready` skips
Celery so a load balancer does not remove a perfectly good instance.

## Frontend data flow

Pages are server components. They fetch from `API_INTERNAL_BASE_URL`
(`http://api:8000` inside compose) at request time; the browser never talks to
the API directly in PHASE 0. `NEXT_PUBLIC_API_BASE_URL` exists for the client
components that later phases need, and by definition holds nothing secret.
