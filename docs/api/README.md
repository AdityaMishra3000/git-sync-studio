# API

Everything is served under `/api/v1`. The OpenAPI document is generated from the
Pydantic schemas and is the authoritative contract:

- <http://localhost:8000/api/v1/openapi.json>
- <http://localhost:8000/docs> (disabled when `APP_ENV=production`)

## Implemented (PHASE 0)

| Method | Path                   | Returns                                                                            |
| ------ | ---------------------- | ---------------------------------------------------------------------------------- |
| `GET`  | `/api/v1/health/live`  | 200 always while the process runs. Touches no dependency.                          |
| `GET`  | `/api/v1/health/ready` | 200 when PostgreSQL and Redis answer, else 503.                                    |
| `GET`  | `/api/v1/health`       | Full report on PostgreSQL, Redis and Celery. 503 if a required dependency is down. |

```console
$ curl -s localhost:8000/api/v1/health | python3 -m json.tool
{
    "status": "ok",
    "service": "gitsync-studio-api",
    "version": "0.1.0",
    "environment": "development",
    "timestamp": "2026-09-02T19:54:19.920555Z",
    "checks": {
        "database": {"status": "ok", "latency_ms": 9.36, "version": "16.15", "detail": "connected", "required": true},
        "redis":    {"status": "ok", "latency_ms": 4.44, "version": "7.4.11", "detail": "connected", "required": true},
        "celery":   {"status": "ok", "latency_ms": 8.53, "version": null, "detail": "1 worker(s) online: celery@5188b60072dd", "required": false}
    }
}
```

## Conventions

- **Versioned prefix.** `/api/v1`. A breaking change means `/api/v2`, not a
  silent alteration.
- **`X-Request-ID`.** Accepted on the way in, generated when absent, always
  echoed back, and bound to every log line for that request.
- **Errors** are JSON: `{"error": "...", "detail": "...", "request_id": "..."}`.
  Stack traces go to the log, never to the client.
- **Snake_case field names**, matching the Pydantic models. The TypeScript
  mirror in `packages/shared-types` keeps them as-is rather than translating.
- **A probe reports, it does not raise.** An unreachable dependency produces a
  described failure, not a 500.

## Planned

Declared here so the contract is visible before it is built. Nothing below
exists yet.

| Phase | Endpoints                                                                                               |
| ----- | ------------------------------------------------------------------------------------------------------- |
| 1     | `GET /repos`, `POST /repos`                                                                             |
| 2     | `GET /auth/github/start`, `GET /auth/github/callback`, `POST /repos/{id}/sync`, `POST /github/webhooks` |
| 3     | `POST /predictions/pull-requests`                                                                       |
| 4     | `POST /drive/upload`, `POST /drive/resolve-pointer`, `GET /drive/download/{oid}`                        |
| 5     | `POST /readme/generate`, `POST /readme/{repoId}/approve`, `GET /readme/{repoId}/versions`               |
