#!/usr/bin/env bash
#
# PHASE 0 Definition of Done, as an executable checklist.
#
#   ./scripts/dev/verify-phase-0.sh
#
# Brings the stack up, then asserts each requirement. Exits non-zero on the
# first failing group so CI can gate on it. Nothing here is destructive: it
# starts containers and reads endpoints.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

WEB_PORT="${WEB_HOST_PORT:-3100}"
API_PORT="${API_HOST_PORT:-8000}"
API="http://localhost:${API_PORT}"
WEB="http://localhost:${WEB_PORT}"

PASSED=0
FAILED=0

pass() {
  printf '  \033[1;32mPASS\033[0m %s\n' "$1"
  PASSED=$((PASSED + 1))
}
fail() {
  printf '  \033[1;31mFAIL\033[0m %s\n' "$1"
  FAILED=$((FAILED + 1))
}
group() { printf '\n\033[1;34m%s\033[0m\n' "$1"; }

check() { # check <description> <command...>
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then pass "$description"; else fail "$description"; fi
}

# Reads one value out of a JSON response with the stdlib; jq is not assumed.
json_get() { # json_get <url> <python-expression-over-`d`>
  curl -fsS --max-time 20 "$1" 2>/dev/null |
    python3 -c "import json,sys; d=json.load(sys.stdin); print($2)" 2>/dev/null
}

expect() { # expect <description> <actual> <wanted>
  if [ "$2" = "$3" ]; then pass "$1 ($2)"; else fail "$1: expected '$3', got '$2'"; fi
}

group "Repository hygiene"
check "compose.yaml is valid" docker compose config --quiet
[ -f .env ] && pass ".env exists" || fail ".env is missing (run scripts/dev/bootstrap.sh)"
if git rev-parse --git-dir >/dev/null 2>&1; then
  tracked_secrets="$(git ls-files | grep -Ec '(^|/)\.env$|\.pem$|credentials\.json$|client_secret.*\.json$' || true)"
  expect "no secret files are tracked by git" "$tracked_secrets" "0"
else
  fail "not a git repository"
fi

group "Bringing the stack up (docker compose up -d --wait)"
if docker compose up -d --wait --wait-timeout 300; then
  pass "all services reported healthy"
else
  fail "at least one service never became healthy"
  docker compose ps
fi

group "Service health"
for service in postgres redis api worker web; do
  state="$(docker compose ps --format '{{.Service}} {{.Health}}' | awk -v s="$service" '$1==s {print $2}')"
  expect "$service container" "${state:-missing}" "healthy"
done

group "FastAPI"
expect "GET /api/v1/health/live is 200" \
  "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/health/live")" "200"
expect "GET /api/v1/health is 200" \
  "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/health")" "200"
expect "aggregate status" "$(json_get "$API/api/v1/health" "d['status']")" "ok"
expect "OpenAPI is served" \
  "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/openapi.json")" "200"
request_id="$(curl -s -o /dev/null -D - -H 'X-Request-ID: verify-phase-0' \
  "$API/api/v1/health/live" | tr -d '\r' | awk 'tolower($1)=="x-request-id:" {print $2}')"
expect "request id is echoed back" "$request_id" "verify-phase-0"

group "Dependencies, as reported by the API"
expect "PostgreSQL" "$(json_get "$API/api/v1/health" "d['checks']['database']['status']")" "ok"
expect "Redis" "$(json_get "$API/api/v1/health" "d['checks']['redis']['status']")" "ok"
expect "Celery worker" "$(json_get "$API/api/v1/health" "d['checks']['celery']['status']")" "ok"
printf '       postgres %s, redis %s, %s\n' \
  "$(json_get "$API/api/v1/health" "d['checks']['database']['version']")" \
  "$(json_get "$API/api/v1/health" "d['checks']['redis']['version']")" \
  "$(json_get "$API/api/v1/health" "d['checks']['celery']['detail']")"

group "Asynchronous path (API -> Redis -> worker -> result backend)"
if docker compose exec -T api python -c "
from app.jobs.celery_app import celery_app
result = celery_app.send_task('ops.ping').get(timeout=30)
assert result['status'] == 'pong', result
" >/dev/null 2>&1; then
  pass "ops.ping executed on the worker and returned a result"
else
  fail "ops.ping did not complete (see: docker compose logs worker)"
fi

group "Database migrations"
check "alembic reaches the database" \
  docker compose exec -T api alembic upgrade head

group "Next.js"
expect "GET / is 200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/")" "200"
expect "GET /dashboard is 200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/dashboard")" "200"
if curl -fsS --max-time 30 "$WEB/dashboard" | grep -q "PostgreSQL"; then
  pass "the dashboard renders live data fetched from the API"
else
  fail "the dashboard did not render API data (backend unreachable from web?)"
fi

group "Result"
printf '  %s passed, %s failed\n\n' "$PASSED" "$FAILED"
if [ "$FAILED" -gt 0 ]; then
  printf '\033[1;31mPHASE 0 is not done.\033[0m\n'
  exit 1
fi
printf '\033[1;32mPHASE 0 Definition of Done satisfied.\033[0m\n'
