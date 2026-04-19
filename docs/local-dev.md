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
5. Start local persistence dependencies when using the default store mode:
   - `docker compose up -d postgres redis`

## Current runtime note

- The default backend store mode is PostgreSQL + Redis.
- Use `MEDDASH_STORE_MODE=inmemory` only for isolated test runs or fallback debugging.
- Use `VITE_API_BASE_URL` in the frontend environment if the backend is not running at `http://127.0.0.1:8000`.

## Local Infra

When Docker daemon is available:

- `docker compose up -d`

This starts:

- PostgreSQL
- Redis
- OpenTelemetry Collector
- Jaeger UI at `http://localhost:16686`

To validate the application images as well:

- `docker compose --profile app build frontend-app backend-app`

## Verification

- Frontend lint: `cd frontend && bun run lint`
- Frontend build/type check: `cd frontend && bun run build`
- Backend lint: `cd backend && uv run ruff check`
- Backend tests: `cd backend && uv run pytest`
- E2E: `cd frontend && bun run e2e`
