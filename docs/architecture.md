# MedDash Architecture

## Layers

- Frontend SPA for clinical workspace
- FastAPI API layer
- LangGraph orchestration layer
- Retrieval and safety services
- Persistence and audit layer
- Observability layer

## Current Runtime Reality

- `frontend/src/App.tsx` queries the backend directly for Knowledge & RAG and Diagnosis & Treatment.
- `backend/src/backend/app.py` boots a PostgreSQL + Redis-backed store by default and supports `MEDDASH_STORE_MODE=inmemory` only as an explicit fallback.
- `backend/src/backend/orchestrator.py` uses persisted sessions and RAG documents for citation retrieval plus diagnosis context composition.
- `backend/src/backend/store.py` keeps PostgreSQL as the durable store for patients, sessions, and RAG documents while Redis caches session payloads for faster reads.

## Target Persistence Split

- PostgreSQL should become the source of truth for durable domain entities: patients, consult sessions, workflow events, audit events, citations, medication alerts, and care-plan outputs.
- Redis should own short-lived operational state: live workflow/session coordination, transient agent status, streaming fan-out buffers, and any cacheable retrieval results.
- Frontend Knowledge & RAG and Diagnosis & Treatment tabs should fetch backend-owned data first and stop depending on `frontend/src/mock-data.ts` for their default display path.

## Safety Model

- Triage and medication checks can block autonomous progression
- Unsafe states must emit handoff packets
- Structured reports must include citations where applicable

## Observability Model

- One correlation ID per consultation request chain
- Trace workflow transitions and agent latency
- Preserve audit events for override and handoff
