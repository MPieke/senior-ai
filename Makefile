.DEFAULT_GOAL := help

COMPOSE := docker compose

.PHONY: help up down logs logs-api logs-web status smoke test test-backend test-frontend test-e2e

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Build and start the application at http://localhost:4173.
	$(COMPOSE) up --build --detach

down: ## Stop application containers (retained analyses stay in the Docker volume).
	$(COMPOSE) down

logs: ## Follow application logs.
	$(COMPOSE) logs --follow

logs-api: ## Follow FastAPI logs only.
	$(COMPOSE) logs --follow api

logs-web: ## Follow frontend logs only.
	$(COMPOSE) logs --follow web

status: ## Show container health and published ports.
	$(COMPOSE) ps

smoke: ## Verify that the API and web application respond.
	curl --fail --retry 10 --retry-connrefused --retry-delay 1 http://localhost:8000/health
	curl --fail --retry 10 --retry-connrefused --retry-delay 1 http://localhost:4173/ > /dev/null

test: ## Run the runtime, backend, and frontend unit tests.
	sh scripts/test-runtime.sh
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Run the FastAPI test suite.
	uv run --directory backend pytest -v

test-frontend: ## Run the React unit test suite.
	npm run test --prefix frontend

test-e2e: ## Run browser tests (install Playwright Chromium first).
	npm run test:e2e --prefix frontend
