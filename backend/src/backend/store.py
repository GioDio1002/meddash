from __future__ import annotations

from collections.abc import Iterable

from backend.models import ConsultSession, PatientProfile, utc_now


class InMemoryStore:
    def __init__(self) -> None:
        self.sessions: dict[str, ConsultSession] = {}
        self.patients: dict[str, PatientProfile] = {}

    def save_patient(self, patient: PatientProfile) -> PatientProfile:
        self.patients[patient.patient_id] = patient
        return patient

    def get_patient(self, patient_id: str) -> PatientProfile | None:
        return self.patients.get(patient_id)

    def save_session(self, session: ConsultSession) -> ConsultSession:
        session.updated_at = utc_now()
        self.sessions[session.session_id] = session
        self.save_patient(session.patient)
        return session

    def get_session(self, session_id: str) -> ConsultSession | None:
        return self.sessions.get(session_id)

    def all_sessions(self) -> Iterable[ConsultSession]:
        return self.sessions.values()

