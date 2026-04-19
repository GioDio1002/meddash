# MedDash API Contract

This document reflects the current runtime contract in source, not the longer-term target architecture.

## Consultation

- `POST /api/consult/start`
  - Body: `{"patient"?: PatientProfile, "opening_message"?: string}`
  - Returns the full `ConsultSession` payload and seeds workflow events.
- `POST /api/consult/chat`
  - Query param: `session_id`
  - Body: `{"message": string}`
  - Returns the updated `ConsultSession`.
- `GET /api/consult/{session_id}`
  - Returns the stored `ConsultSession` or `404`.
- `GET /api/consult/{session_id}/events`
  - Returns server-sent events for the session's recorded workflow steps.

## Agents

- `GET /api/agents/status`
  - Returns synthetic agent state derived from the latest in-memory session.

## RAG

- `POST /api/rag/query`
  - Body: `{"session_id"?: string, "query": string}`
  - Returns orchestrator-generated citations for the query.
  - Current limitation: citations are generated in code and are not backed by PostgreSQL, Redis, or a document index.

## Clinical Outputs

- `POST /api/diagnosis/generate`
  - Body: `{"session_id"?: string, "symptoms": string[], "notes"?: string}`
  - Returns an orchestrator-generated care plan report.
  - Current limitation: diagnosis output is not durably persisted outside the active in-memory session.
- `POST /api/patient/save`
  - Body: `{"patient": PatientProfile}`
  - Saves the patient to the current in-process store.
- `POST /api/workflows/{session_id}/handoff`
  - Body: `{"actor"?: string, "reason": string}`
  - Marks the session as needing handoff and appends an audit event.

## Not Yet Implemented

- `POST /api/rag/documents`
- `GET /api/prompts`
