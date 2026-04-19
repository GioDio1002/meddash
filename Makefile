PYTHON ?= /opt/homebrew/bin/python3.12

.PHONY: frontend-install backend-sync dev-frontend dev-backend lint test e2e

frontend-install:
	cd frontend && bun install --frozen-lockfile

backend-sync:
	cd backend && uv sync --frozen --python $(PYTHON)

dev-frontend:
	cd frontend && bun dev --host

dev-backend:
	cd backend && uv run uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

lint:
	cd frontend && bun run lint
	cd backend && uv run ruff check

test:
	cd backend && uv run pytest

e2e:
	cd frontend && bun run e2e
