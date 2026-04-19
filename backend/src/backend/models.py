from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    NEEDS_HANDOFF = "needs_handoff"
    COMPLETED = "completed"


class UrgencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


URGENCY_ORDER: dict[UrgencyLevel, int] = {
    UrgencyLevel.LOW: 0,
    UrgencyLevel.MEDIUM: 1,
    UrgencyLevel.HIGH: 2,
    UrgencyLevel.CRITICAL: 3,
}


class AgentState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"


class CitationSourceType(StrEnum):
    GUIDELINE = "guideline"
    DRUG_LABEL = "drug_label"
    CASE = "case"


class MessageRole(StrEnum):
    PATIENT = "patient"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class PatientProfile(BaseModel):
    patient_id: str = Field(default_factory=lambda: new_id("patient"))
    full_name: str | None = None
    age: int | None = None
    sex: Literal["female", "male", "other", "unknown"] = "unknown"
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ConsultMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: new_id("msg"))
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class StructuredIntake(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    medical_history: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


class TriageDecision(BaseModel):
    department: str = "general_medicine"
    urgency: UrgencyLevel = UrgencyLevel.LOW
    rationale: str = "Awaiting intake."
    handoff_required: bool = False


class EvidenceCitation(BaseModel):
    citation_id: str = Field(default_factory=lambda: new_id("cite"))
    title: str
    source_type: CitationSourceType
    snippet: str
    relevance: float = 0.5


class RagDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: new_id("doc"))
    title: str
    source_type: CitationSourceType
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MedicationAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: new_id("medalert"))
    medication: str
    severity: Literal["info", "warning", "blocking"] = "info"
    message: str


class DiagnosisCandidate(BaseModel):
    label: str
    confidence: float
    rationale: str


class CarePlanReport(BaseModel):
    report_id: str = Field(default_factory=lambda: new_id("report"))
    summary: str
    differential: list[DiagnosisCandidate] = Field(default_factory=list)
    recommended_tests: list[str] = Field(default_factory=list)
    follow_up_plan: str = "Monitor symptoms and follow clinician guidance."
    citations: list[EvidenceCitation] = Field(default_factory=list)
    medication_alerts: list[MedicationAlert] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("audit"))
    action: str
    actor: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class WorkflowEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    session_id: str
    step: str
    agent: str
    state: AgentState
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ConsultSession(BaseModel):
    session_id: str = Field(default_factory=lambda: new_id("session"))
    patient: PatientProfile
    status: SessionStatus = SessionStatus.ACTIVE
    messages: list[ConsultMessage] = Field(default_factory=list)
    intake: StructuredIntake = Field(default_factory=StructuredIntake)
    triage: TriageDecision = Field(default_factory=TriageDecision)
    citations: list[EvidenceCitation] = Field(default_factory=list)
    medication_alerts: list[MedicationAlert] = Field(default_factory=list)
    care_plan: CarePlanReport | None = None
    audit_events: list[AuditEvent] = Field(default_factory=list)
    workflow_events: list[WorkflowEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StartConsultRequest(BaseModel):
    patient: PatientProfile | None = None
    opening_message: str | None = None


class ChatRequest(BaseModel):
    message: str


class RagQueryRequest(BaseModel):
    session_id: str | None = None
    query: str


class RagQueryResponse(BaseModel):
    query: str
    citations: list[EvidenceCitation]


class RagDocumentInput(BaseModel):
    title: str
    source_type: CitationSourceType
    content: str
    tags: list[str] = Field(default_factory=list)


class RagDocumentUpsertRequest(BaseModel):
    documents: list[RagDocumentInput]


class RagDocumentUpsertResponse(BaseModel):
    documents: list[RagDocument]


class DiagnosisRequest(BaseModel):
    session_id: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    notes: str | None = None


class PatientSaveRequest(BaseModel):
    patient: PatientProfile


class WorkflowHandoffRequest(BaseModel):
    actor: str = "clinician"
    reason: str


class AgentStatusItem(BaseModel):
    agent: str
    state: AgentState
    active_session_id: str | None = None
