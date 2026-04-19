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
   - `make dev-backend`

## Local Infra

When Docker daemon is available:

- `docker compose up -d`

This starts:

- PostgreSQL
- Redis
- OpenTelemetry Collector
- Jaeger UI at `http://localhost:16686`

## Verification

- Frontend lint: `cd frontend && bun run lint`
- Backend lint: `cd backend && uv run ruff check`
- Backend tests: `cd backend && uv run pytest`
- E2E: `cd frontend && bunx playwright test`
