# MedDash API Contract

## Consultation

- `POST /api/consult/start`
- `POST /api/consult/chat`
- `GET /api/consult/{session_id}`
- `GET /api/consult/{session_id}/events`

## Agents

- `GET /api/agents/status`

## RAG

- `POST /api/rag/query`
- `POST /api/rag/documents`

## Clinical Outputs

- `POST /api/diagnosis/generate`
- `POST /api/patient/save`
- `POST /api/workflows/{session_id}/handoff`

## Prompt Ops

- `GET /api/prompts`
