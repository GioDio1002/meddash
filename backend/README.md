# MedDash Backend

FastAPI backend for the clinician-assistive MedDash prototype.

## Current implementation status

- The default app store is `backend.store.PostgresRedisStore`.
- PostgreSQL persists patients, consultation sessions, and RAG documents.
- Redis caches session payloads for faster repeated session reads.
- Set `MEDDASH_STORE_MODE=inmemory` only for isolated test or fallback runs.

## Run

```bash
uv run --directory backend uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

To use the default persistent store locally, start `postgres` and `redis` first:

```bash
docker compose up -d postgres redis
```

## Test

```bash
uv run --directory backend pytest
uv run --directory backend ruff check .
```
