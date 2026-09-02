#!/usr/bin/env bash
#
# One-time setup for a fresh clone.
#
#   ./scripts/dev/bootstrap.sh
#
# Idempotent: safe to re-run after pulling changes to dependencies.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

info() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m warn\033[0m %s\n' "$1"; }
die() {
  printf '\033[1;31merror\033[0m %s\n' "$1" >&2
  exit 1
}

# --- prerequisites --------------------------------------------------------
info "Checking prerequisites"
command -v docker >/dev/null || die "docker is not installed"
docker compose version >/dev/null 2>&1 || die "the docker compose plugin is not installed"
command -v node >/dev/null || die "node is not installed (>= 20.9 required)"
command -v python3 >/dev/null || die "python3 is not installed (>= 3.12 required)"

node_major="$(node --version | sed 's/^v\([0-9]*\).*/\1/')"
[ "$node_major" -ge 20 ] || die "node $(node --version) is too old; 20.9+ required"

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' ||
  die "python $(python3 --version) is too old; 3.12+ required"

# --- environment file -----------------------------------------------------
if [ -f .env ]; then
  info ".env already exists, leaving it alone"
else
  info "Creating .env from .env.example"
  cp .env.example .env
  warn "Edit .env before deploying anywhere: SECRET_KEY is a development placeholder."
fi

# --- python -------------------------------------------------------------
if [ ! -d .venv ]; then
  info "Creating .venv"
  python3 -m venv .venv
fi

info "Installing the API (editable) and its dev dependencies"
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -e "apps/api[dev]"

# --- node ---------------------------------------------------------------
info "Installing npm workspaces (web + shared-types)"
npm install --silent

cat <<'NEXT'

Bootstrap complete.

  docker compose up --build          start the whole stack
  ./scripts/dev/verify-phase-0.sh    assert every PHASE 0 requirement

  web  http://localhost:3100
  api  http://localhost:8000/docs

Python tooling lives in .venv, so prefix commands with it or activate it:

  source .venv/bin/activate
NEXT
