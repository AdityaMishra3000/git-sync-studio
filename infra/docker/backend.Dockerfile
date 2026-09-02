# syntax=docker/dockerfile:1
#
# Backend image: serves both the FastAPI API and the Celery worker.
#
# One image, two commands. GitSync Studio is a modular monolith: a job and the
# request handler that queued it share models, settings and adapters, so shipping
# two images built from the same source would only create drift. The processes
# stay separate (see compose.yaml) so heavy jobs cannot block HTTP.
#
# Build context is the repository ROOT:
#   docker build -f infra/docker/backend.Dockerfile --target dev .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/srv/api:/srv/worker

# curl is here for the container healthcheck and for debugging inside the container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# uid 1000 matches the usual first Linux desktop user, so files written into a
# bind mount during development stay owned by the developer, not by root.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

WORKDIR /srv/api

# --------------------------------------------------------------------------
# Runtime dependencies. Installed from pyproject.toml alone, against a stub
# package, so editing source does not invalidate this layer.
# --------------------------------------------------------------------------
FROM base AS deps-runtime

COPY apps/api/pyproject.toml /srv/api/pyproject.toml
RUN mkdir -p /srv/api/app \
    && touch /srv/api/app/__init__.py \
    && printf 'placeholder\n' > /srv/api/README.md \
    && pip install -e /srv/api

# --------------------------------------------------------------------------
# Development dependencies on top (pytest, ruff, mypy).
# --------------------------------------------------------------------------
FROM deps-runtime AS deps-dev
RUN pip install -e "/srv/api[dev]"

# --------------------------------------------------------------------------
# Development target: reload server, test tooling present. compose bind-mounts
# the source over these copies; the COPY keeps the image runnable without them.
# --------------------------------------------------------------------------
FROM deps-dev AS dev

COPY --chown=app:app apps/api /srv/api
COPY --chown=app:app apps/worker /srv/worker

USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --------------------------------------------------------------------------
# Production target: no dev tooling, no reload, non-root.
# --------------------------------------------------------------------------
FROM deps-runtime AS runtime

COPY --chown=app:app apps/api /srv/api
COPY --chown=app:app apps/worker /srv/worker

USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
