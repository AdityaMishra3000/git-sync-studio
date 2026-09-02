.DEFAULT_GOAL := help
.PHONY: help bootstrap up down restart logs ps verify lint format typecheck test test-int test-e2e migrate migration api-shell db-shell clean

RUFF := ./.venv/bin/ruff
MYPY := ../../.venv/bin/mypy
PYTEST := ../../.venv/bin/pytest

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1;36m%-14s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Set up .env, the virtualenv and npm workspaces
	./scripts/dev/bootstrap.sh

up: ## Start the whole stack and wait for it to be healthy
	docker compose up -d --build --wait

down: ## Stop the stack (keeps database and redis volumes)
	docker compose down

restart: ## Restart the api and worker (after changing backend code)
	docker compose restart api worker

logs: ## Follow logs for every service
	docker compose logs -f

ps: ## Show service status
	docker compose ps

verify: ## Assert every PHASE 0 Definition of Done item
	./scripts/dev/verify-phase-0.sh

lint: ## Lint everything (ruff + eslint + prettier check)
	$(RUFF) check apps/api apps/worker
	$(RUFF) format --check apps/api apps/worker
	npm run lint
	npx prettier --check .

format: ## Auto-format everything (ruff + prettier)
	$(RUFF) check --fix apps/api apps/worker
	$(RUFF) format apps/api apps/worker
	npx prettier --write .

typecheck: ## Static types (mypy --strict + tsc)
	cd apps/api && $(MYPY)
	npm run typecheck

test: ## Unit and component tests (pytest + vitest)
	cd apps/api && $(PYTEST)
	npm test

test-int: ## Integration tests; needs the stack running
	cd apps/api && RUN_INTEGRATION_TESTS=1 $(PYTEST) -m integration

test-e2e: ## Playwright end-to-end tests; needs the stack running
	E2E_BASE_URL=http://localhost:$${WEB_HOST_PORT:-3100} npm run test:e2e

migrate: ## Apply migrations inside the api container
	docker compose exec api alembic upgrade head

migration: ## Autogenerate a migration: make migration m="add users"
	docker compose exec api alembic revision --autogenerate -m "$(m)"

api-shell: ## Python REPL inside the api container
	docker compose exec api python

db-shell: ## psql inside the postgres container
	docker compose exec postgres psql -U $${POSTGRES_USER:-gitsync} -d $${POSTGRES_DB:-gitsync}

clean: ## Stop the stack and DELETE the database and redis volumes
	@printf 'This destroys the local database. Continue? [y/N] ' && read ans && [ "$$ans" = "y" ]
	docker compose down -v
