# Local Development

## Prerequisites

- Bun
- Node
- Python 3.12.11
- uv
- Playwright
- Docker Desktop or another reachable Docker daemon

## Bootstrap

1. Install frontend dependencies:
   - `make frontend-install`
2. Sync backend dependencies:
   - `make backend-sync`
3. Start frontend:
   - `make dev-frontend`
4. Start backend:
   - `cd backend && uv run uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`

## Current runtime note

- PostgreSQL and Redis are provisioned for the next persistence migration step, but the backend currently runs against the in-process `InMemoryStore`.
- Because of that, you can exercise the current API and frontend shell without Docker if you only need the prototype behavior.
- Use `VITE_API_BASE_URL` in the frontend environment if the backend is not running at `http://127.0.0.1:8000`.

## Local Infra

When Docker daemon is available:

- `docker compose up -d`

This starts:

- PostgreSQL
- Redis
- OpenTelemetry Collector
- Jaeger UI at `http://localhost:16686`

At the moment those services are infrastructure-only; the checked-in backend code does not yet open PostgreSQL or Redis connections on startup.

## Verification

- Frontend lint: `cd frontend && bun run lint`
- Frontend build/type check: `cd frontend && bun run build`
- Backend lint: `cd backend && uv run ruff check`
- Backend tests: `cd backend && uv run pytest`
- E2E: `cd frontend && bunx playwright test`
