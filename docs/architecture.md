# MedDash Architecture

## Layers

- Frontend SPA for clinical workspace
- FastAPI API layer
- LangGraph orchestration layer
- Retrieval and safety services
- Persistence and audit layer
- Observability layer

## Current Runtime Reality

- `frontend/src/App.tsx` starts a real consultation through the backend, but the Knowledge & RAG and Diagnosis & Treatment tabs still fall back to `frontend/src/mock-data.ts` when no live session has been created.
- `backend/src/backend/app.py` wires `InMemoryStore` directly into application state.
- `backend/src/backend/orchestrator.py` depends on that same store for sessions, patients, and derived agent status.
- `backend/src/backend/store.py` keeps all sessions and patient records in Python dictionaries, so data is lost on restart and cannot be shared across backend workers.

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
