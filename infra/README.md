# infra/

Infrastructure definitions. The Compose file that ties them together lives at the
repository root (`compose.yaml`) because that is where `docker compose` expects it.

```text
docker/backend.Dockerfile   API and Celery worker (one image, two commands)
docker/web.Dockerfile       Next.js, dev + standalone production targets
```

Both build with the **repository root as context**, which is why `.dockerignore`
lives at the root too. The backend image needs `apps/api` and `apps/worker`; the
web image needs the root lockfile and the `packages/shared-types` workspace.

Each Dockerfile has a `dev` target (reload, dev tooling, source bind-mounted by
Compose) and a production target (`runtime`) that runs as an unprivileged user
with no dev dependencies. Compose uses `dev`; PHASE 9 CI builds `runtime` and
publishes it to GHCR.
