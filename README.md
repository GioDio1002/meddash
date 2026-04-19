# MedDash

MedDash is a clinician-assistive medical multi-agent system built with a React frontend and a FastAPI + LangGraph backend.

## Stack

- Frontend: Bun, Vite, React, TypeScript, Ant Design
- Backend: Python 3.12.11, FastAPI, LangGraph
- Data: PostgreSQL-backed durable session/document storage with Redis session cache
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

- Patient consultation uses live backend endpoints and stores sessions in PostgreSQL with Redis-backed session caching.
- Knowledge & RAG now queries backend-owned documents through `POST /api/rag/query`.
- Diagnosis & Treatment now renders backend-generated care plans through `POST /api/diagnosis/generate`.
- `POST /api/rag/documents` is implemented for document ingestion and seeds default medical guidance on first startup.

## Implemented APIs

- `POST /api/consult/start`
- `POST /api/consult/chat`
- `GET /api/consult/{session_id}`
- `GET /api/consult/{session_id}/events`
- `GET /api/agents/status`
- `POST /api/rag/query`
- `POST /api/rag/documents`
- `POST /api/diagnosis/generate`
- `POST /api/patient/save`
- `POST /api/workflows/{session_id}/handoff`
- `GET /api/prompts`

## Local Development

The repository is bootstrapped in phases:

1. Root repo contract and planning artifacts
2. Frontend and backend scaffolds
3. Domain contracts and orchestration
4. Observability and testing
5. E2E verification

Docker Compose now supports both infra-only startup and app-image builds:

- `docker compose up -d postgres redis` for local backend dependencies only
- `docker compose --profile app build frontend-app backend-app` to validate the application images
