# MedDash Architecture

## Layers

- Frontend SPA for clinical workspace
- FastAPI API layer
- LangGraph orchestration layer
- Retrieval and safety services
- Persistence and audit layer
- Observability layer

## Safety Model

- Triage and medication checks can block autonomous progression
- Unsafe states must emit handoff packets
- Structured reports must include citations where applicable

## Observability Model

- One correlation ID per consultation request chain
- Trace workflow transitions and agent latency
- Preserve audit events for override and handoff
