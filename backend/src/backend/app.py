from __future__ import annotations

import json
import logging
from collections.abc import Iterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from backend.models import (
    ChatRequest,
    DiagnosisRequest,
    PatientSaveRequest,
    RagQueryRequest,
    StartConsultRequest,
    WorkflowHandoffRequest,
)
from backend.orchestrator import ConsultOrchestrator
from backend.store import InMemoryStore


def configure_telemetry() -> None:
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        trace.set_tracer_provider(TracerProvider())


def create_app() -> FastAPI:
    configure_telemetry()
    app = FastAPI(title="MedDash Backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    FastAPIInstrumentor.instrument_app(app)
    app.state.store = InMemoryStore()
    app.state.orchestrator = ConsultOrchestrator(app.state.store)
    app.state.logger = logging.getLogger("meddash.backend")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/consult/start")
    def start_consult(request: StartConsultRequest) -> dict:
        session = app.state.orchestrator.start_consult(request)
        return session.model_dump(mode="json")

    @app.post("/api/consult/chat")
    def consult_chat(request: ChatRequest, session_id: str) -> dict:
        try:
            session = app.state.orchestrator.handle_chat(session_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        return session.model_dump(mode="json")

    @app.get("/api/consult/{session_id}")
    def get_consult(session_id: str) -> dict:
        session = app.state.store.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.model_dump(mode="json")

    @app.get("/api/consult/{session_id}/events")
    def get_consult_events(session_id: str, request: Request) -> StreamingResponse:
        session = app.state.store.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        def stream() -> Iterator[str]:
            for event in session.workflow_events:
                yield (
                    f"event: workflow.step\n"
                    f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
                )

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/api/agents/status")
    def agents_status() -> dict[str, list[dict]]:
        return {"agents": app.state.orchestrator.agent_status()}

    @app.post("/api/rag/query")
    def rag_query(request: RagQueryRequest) -> dict:
        citations = app.state.orchestrator.rag_query(request.query)
        return {"query": request.query, "citations": [c.model_dump(mode="json") for c in citations]}

    @app.post("/api/diagnosis/generate")
    def diagnosis_generate(request: DiagnosisRequest) -> dict:
        report = app.state.orchestrator.generate_diagnosis(
            request.session_id,
            request.symptoms,
            request.notes,
        )
        return report.model_dump(mode="json")

    @app.post("/api/patient/save")
    def patient_save(request: PatientSaveRequest) -> dict:
        patient = app.state.store.save_patient(request.patient)
        return {"patient": patient.model_dump(mode="json")}

    @app.post("/api/workflows/{session_id}/handoff")
    def workflow_handoff(session_id: str, request: WorkflowHandoffRequest) -> dict:
        try:
            session = app.state.orchestrator.handoff(session_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        return session.model_dump(mode="json")

    return app


app = create_app()
