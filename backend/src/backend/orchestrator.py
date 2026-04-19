from __future__ import annotations

from typing import Any

from backend.models import (
    URGENCY_ORDER,
    AgentState,
    CarePlanReport,
    ChatRequest,
    ConsultMessage,
    ConsultSession,
    DiagnosisCandidate,
    EvidenceCitation,
    MedicationAlert,
    MessageRole,
    PatientProfile,
    SessionStatus,
    StartConsultRequest,
    TriageDecision,
    UrgencyLevel,
    WorkflowEvent,
    WorkflowHandoffRequest,
)
from backend.store import InMemoryStore


class ConsultOrchestrator:
    AGENTS: tuple[str, ...] = (
        "IntakeAgent",
        "TriageAgent",
        "KnowledgeRAGAgent",
        "DiagnosisAgent",
        "MedicationSafetyAgent",
        "SummaryAgent",
        "HandoffAgent",
    )

    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def start_consult(self, request: StartConsultRequest) -> ConsultSession:
        patient = request.patient or PatientProfile()
        session = ConsultSession(patient=patient)
        if request.opening_message:
            session.messages.append(
                ConsultMessage(role=MessageRole.PATIENT, content=request.opening_message)
            )
        self._append_event(
            session,
            step="consult_started",
            agent="IntakeAgent",
            state=AgentState.COMPLETED,
            detail="Consultation session created.",
            payload={"patient_id": patient.patient_id},
        )
        if request.opening_message:
            self._run_flow(session, request.opening_message)
        return self.store.save_session(session)

    def handle_chat(self, session_id: str, request: ChatRequest) -> ConsultSession:
        session = self._require_session(session_id)
        session.messages.append(ConsultMessage(role=MessageRole.PATIENT, content=request.message))
        self._run_flow(session, request.message)
        return self.store.save_session(session)

    def rag_query(self, query: str) -> list[EvidenceCitation]:
        return self._build_citations(query)

    def generate_diagnosis(
        self, session_id: str | None, symptoms: list[str], notes: str | None
    ) -> CarePlanReport:
        source_text = " ".join([*symptoms, notes or ""]).strip() or "general consultation"
        citations = self._build_citations(source_text)
        alerts = self._build_medication_alerts(source_text)
        return self._build_care_plan(source_text, citations, alerts)

    def handoff(self, session_id: str, request: WorkflowHandoffRequest) -> ConsultSession:
        session = self._require_session(session_id)
        session.status = SessionStatus.NEEDS_HANDOFF
        session.audit_events.append(
            self._build_audit(
                action="workflow_handoff",
                actor=request.actor,
                details={"reason": request.reason},
            )
        )
        self._append_event(
            session,
            step="handoff_requested",
            agent="HandoffAgent",
            state=AgentState.COMPLETED,
            detail=request.reason,
            payload={"actor": request.actor},
        )
        return self.store.save_session(session)

    def agent_status(self) -> list[dict[str, Any]]:
        latest_session = max(
            self.store.all_sessions(),
            key=lambda session: session.updated_at,
            default=None,
        )
        active_session = (
            latest_session.session_id
            if latest_session and latest_session.status != SessionStatus.COMPLETED
            else None
        )
        return [
            {
                "agent": agent,
                "state": (
                    AgentState.COMPLETED
                    if latest_session and latest_session.workflow_events
                    else AgentState.IDLE
                )
                if not active_session
                else AgentState.RUNNING,
                "active_session_id": active_session,
            }
            for agent in self.AGENTS
        ]

    def _require_session(self, session_id: str) -> ConsultSession:
        session = self.store.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def _run_flow(self, session: ConsultSession, message: str) -> None:
        self._append_event(
            session,
            step="intake_collected",
            agent="IntakeAgent",
            state=AgentState.COMPLETED,
            detail="Structured intake updated from patient message.",
            payload={"message_excerpt": message[:120]},
        )
        self._update_intake(session, message)

        triage = self._merge_triage(session.triage, self._build_triage(message))
        session.triage = triage
        session.status = (
            SessionStatus.NEEDS_HANDOFF if triage.handoff_required else SessionStatus.ACTIVE
        )
        self._append_event(
            session,
            step="triage_completed",
            agent="TriageAgent",
            state=AgentState.COMPLETED,
            detail=triage.rationale,
            payload=triage.model_dump(mode="json"),
        )

        citations = self._build_citations(message)
        session.citations = citations
        self._append_event(
            session,
            step="rag_retrieved",
            agent="KnowledgeRAGAgent",
            state=AgentState.COMPLETED,
            detail="Retrieved structured knowledge citations for the current message.",
            payload={"citation_count": len(citations)},
        )

        alerts = self._build_medication_alerts(message)
        session.medication_alerts = alerts
        self._append_event(
            session,
            step="medication_safety_checked",
            agent="MedicationSafetyAgent",
            state=AgentState.COMPLETED,
            detail="Medication safety checks completed.",
            payload={"alert_count": len(alerts)},
        )
        if any(alert.severity == "blocking" for alert in alerts):
            session.status = SessionStatus.NEEDS_HANDOFF

        care_plan = self._build_care_plan(message, citations, alerts)
        session.care_plan = care_plan
        self._append_event(
            session,
            step="diagnosis_generated",
            agent="DiagnosisAgent",
            state=AgentState.COMPLETED,
            detail="Generated clinician-assistive care plan.",
            payload={"report_id": care_plan.report_id},
        )
        self._append_event(
            session,
            step="summary_completed",
            agent="SummaryAgent",
            state=AgentState.COMPLETED,
            detail="Summary report ready for review.",
            payload={"status": session.status},
        )

        session.audit_events.append(
            self._build_audit(
                action="consultation_updated",
                actor="system",
                details={
                    "session_id": session.session_id,
                    "urgency": triage.urgency,
                    "blocking_alerts": [
                        alert.alert_id for alert in alerts if alert.severity == "blocking"
                    ],
                },
            )
        )

    def _update_intake(self, session: ConsultSession, message: str) -> None:
        lowered = message.lower()
        symptom_tokens = [
            token
            for token in ["fever", "cough", "chest pain", "shortness of breath", "headache", "rash"]
            if token in lowered
        ]
        if not symptom_tokens:
            symptom_tokens = [message[:80]]
        allergies = list(dict.fromkeys([*session.patient.allergies, *session.intake.allergies]))
        if "penicillin" in lowered and "allergic" in lowered and "penicillin" not in allergies:
            allergies.append("penicillin")
        red_flags = list(session.intake.red_flags)
        for token in ["chest pain", "shortness of breath", "severe bleeding"]:
            if token in lowered and token not in red_flags:
                red_flags.append(token)
        session.intake.symptoms = symptom_tokens
        session.intake.allergies = allergies
        session.patient.allergies = allergies
        session.intake.red_flags = red_flags

    def _merge_triage(
        self, existing: TriageDecision, proposed: TriageDecision
    ) -> TriageDecision:
        if URGENCY_ORDER[proposed.urgency] >= URGENCY_ORDER[existing.urgency]:
            return proposed
        return TriageDecision(
            department=existing.department,
            urgency=existing.urgency,
            rationale=(
                f"{existing.rationale} Higher-acuity triage remains in force despite "
                "lower-risk follow-up text."
            ),
            handoff_required=existing.handoff_required or proposed.handoff_required,
        )

    def _build_triage(self, message: str) -> TriageDecision:
        lowered = message.lower()
        if "chest pain" in lowered or "shortness of breath" in lowered:
            return TriageDecision(
                department="emergency",
                urgency=UrgencyLevel.CRITICAL,
                rationale="Potential cardiopulmonary red flag detected; escalate to clinician.",
                handoff_required=True,
            )
        if "fever" in lowered or "cough" in lowered:
            return TriageDecision(
                department="internal_medicine",
                urgency=UrgencyLevel.MEDIUM,
                rationale="Symptoms suggest general internal medicine evaluation.",
                handoff_required=False,
            )
        return TriageDecision(
            department="general_medicine",
            urgency=UrgencyLevel.LOW,
            rationale="No immediate red flag detected in current message.",
            handoff_required=False,
        )

    def _build_citations(self, query: str) -> list[EvidenceCitation]:
        topic = query[:64] or "consultation"
        return [
            EvidenceCitation(
                title="Triage Red Flag Guidance",
                source_type="guideline",
                snippet=f"Escalate urgent presentations when symptoms resemble: {topic}.",
                relevance=0.91,
            ),
            EvidenceCitation(
                title="Medication Contraindication Note",
                source_type="drug_label",
                snippet="Review allergies and current medications before recommending treatment.",
                relevance=0.82,
            ),
        ]

    def _build_medication_alerts(self, text: str) -> list[MedicationAlert]:
        lowered = text.lower()
        alerts: list[MedicationAlert] = []
        if "penicillin" in lowered and ("amoxicillin" in lowered or "augmentin" in lowered):
            alerts.append(
                MedicationAlert(
                    medication="amoxicillin",
                    severity="blocking",
                    message=(
                        "Potential penicillin allergy conflict detected; "
                        "clinician review required."
                    ),
                )
            )
        if "warfarin" in lowered and "ibuprofen" in lowered:
            alerts.append(
                MedicationAlert(
                    medication="ibuprofen",
                    severity="warning",
                    message="Possible bleeding-risk interaction with warfarin.",
                )
            )
        return alerts

    def _build_care_plan(
        self,
        message: str,
        citations: list[EvidenceCitation],
        alerts: list[MedicationAlert],
    ) -> CarePlanReport:
        lowered = message.lower()
        if "cough" in lowered or "fever" in lowered:
            differential = [
                DiagnosisCandidate(
                    label="Upper respiratory infection",
                    confidence=0.63,
                    rationale=(
                        "Symptoms suggest an infectious but non-specific "
                        "respiratory presentation."
                    ),
                )
            ]
            tests = ["Vital signs review", "Respiratory examination"]
        elif "chest pain" in lowered:
            differential = [
                DiagnosisCandidate(
                    label="Acute chest pain syndrome",
                    confidence=0.71,
                    rationale="Requires urgent exclusion of high-risk cardiopulmonary causes.",
                )
            ]
            tests = ["ECG", "Troponin", "Pulse oximetry"]
        else:
            differential = [
                DiagnosisCandidate(
                    label="General symptom review required",
                    confidence=0.4,
                    rationale="Insufficient specificity; clinician review recommended.",
                )
            ]
            tests = ["Focused history", "Basic physical exam"]
        return CarePlanReport(
            summary=(
                "Clinician-assistive recommendation generated from current "
                "consultation context."
            ),
            differential=differential,
            recommended_tests=tests,
            follow_up_plan="Escalate to clinician if symptoms worsen or any red flag is present.",
            citations=citations,
            medication_alerts=alerts,
        )

    def _build_audit(self, action: str, actor: str, details: dict[str, Any]) -> Any:
        from backend.models import AuditEvent

        return AuditEvent(action=action, actor=actor, details=details)

    def _append_event(
        self,
        session: ConsultSession,
        *,
        step: str,
        agent: str,
        state: AgentState,
        detail: str,
        payload: dict[str, Any],
    ) -> None:
        session.workflow_events.append(
            WorkflowEvent(
                session_id=session.session_id,
                step=step,
                agent=agent,
                state=state,
                detail=detail,
                payload=payload,
            )
        )
