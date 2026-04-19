# MedDash API Contract

This document reflects the current runtime contract in source.

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
  - Returns synthetic agent state derived from the latest persisted consultation session.

## RAG

- `POST /api/rag/query`
  - Body: `{"session_id"?: string, "query": string}`
  - Returns citations resolved from PostgreSQL-backed RAG documents.
- `POST /api/rag/documents`
  - Body: `{"documents": [{"title": string, "source_type": "guideline" | "drug_label" | "case", "content": string, "tags"?: string[]}]}`
  - Upserts document records for later retrieval via `POST /api/rag/query`.

## Clinical Outputs

- `POST /api/diagnosis/generate`
  - Body: `{"session_id"?: string, "symptoms": string[], "notes"?: string}`
  - Returns an orchestrator-generated care plan report using persisted citations plus session context when `session_id` is provided.
- `POST /api/patient/save`
  - Body: `{"patient": PatientProfile}`
  - Saves the patient to PostgreSQL.
- `POST /api/workflows/{session_id}/handoff`
  - Body: `{"actor"?: string, "reason": string}`
  - Marks the session as needing handoff and appends an audit event.

## Not Yet Implemented

- `GET /api/prompts`
