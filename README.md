# MedDash

MedDash is a clinician-assistive medical multi-agent system built with a React frontend and a FastAPI + LangGraph backend.

## Stack

- Frontend: Bun, Vite, React, TypeScript, Ant Design
- Backend: Python 3.12.11, FastAPI, LangGraph
- Current runtime persistence: in-process Python memory
- Provisioned infra for next migration step: PostgreSQL, Redis
- Testing: Playwright, pytest
- Observability: OpenTelemetry
- Prompt Ops: Agenta adapter support, disabled by default

## Product Scope

The initial version includes:

1. Dashboard
2. Patient Consultation
3. Medical Knowledge and RAG
4. Diagnosis and Treatment Recommendation
5. Workflow and Task Center
6. Settings and Prompt Ops

## Safety Boundary

MedDash is a clinical decision support tool. It does not replace licensed medical judgment and must escalate urgent or unsafe cases to a clinician workflow.

## Current implementation status

- Patient consultation uses live backend endpoints today.
- Knowledge & RAG and Diagnosis & Treatment can render live backend-derived data when a real consultation session exists, but the default shell still falls back to `frontend/src/mock-data.ts`.
- Backend persistence is still wired through `backend/src/backend/store.py:InMemoryStore`; PostgreSQL and Redis are provisioned in `compose.yaml` but are not yet the active runtime store.
- `POST /api/rag/query` and `POST /api/diagnosis/generate` return orchestrator-generated results, not persisted document retrieval or durable workflow state.

See `docs/architecture.md` and `docs/api-contract.md` for the current-vs-target split that the real-backend migration should close.

## Implemented APIs

- `POST /api/consult/start`
- `POST /api/consult/chat`
- `GET /api/consult/{session_id}`
- `GET /api/consult/{session_id}/events`
- `GET /api/agents/status`
- `POST /api/rag/query`
- `POST /api/diagnosis/generate`
- `POST /api/patient/save`
- `POST /api/workflows/{session_id}/handoff`

## Not yet implemented APIs

- `POST /api/rag/documents`
- `GET /api/prompts`

## Local Development

The repository is bootstrapped in phases:

1. Root repo contract and planning artifacts
2. Frontend and backend scaffolds
3. Domain contracts and orchestration
4. Observability and testing
5. E2E verification

Docker Compose is part of the target workflow, but local Docker daemon readiness must be verified before containerized services are used. Today the application can run without Docker because the backend still uses the in-process store.
