from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import Protocol

import psycopg
from redis import Redis
from redis.exceptions import RedisError

from backend.models import (
    ConsultSession,
    EvidenceCitation,
    PatientProfile,
    RagDocument,
    RagDocumentInput,
    utc_now,
)

DEFAULT_RAG_DOCUMENTS: tuple[RagDocumentInput, ...] = (
    RagDocumentInput(
        title="ACC/AHA Acute Coronary Syndrome Guideline",
        source_type="guideline",
        content=(
            "Immediate urgent evaluation is recommended for acute chest pain with dyspnea, "
            "presyncope, or other cardiopulmonary red-flag symptoms."
        ),
        tags=["cardiology", "triage", "chest pain"],
    ),
    RagDocumentInput(
        title="Aspirin Prescribing Information",
        source_type="drug_label",
        content=(
            "Review hypersensitivity history, active gastrointestinal bleeding risk, and current "
            "medication list before recommending aspirin therapy."
        ),
        tags=["medication safety", "aspirin", "allergy"],
    ),
    RagDocumentInput(
        title="Internal Similar Case Review - ED Transfer",
        source_type="case",
        content=(
            "Patients with chest tightness, dizziness, and shortness of breath were routed to "
            "emergency evaluation pending ECG, troponin testing, and clinician review."
        ),
        tags=["case review", "ed transfer", "shortness of breath"],
    ),
)


class StoreProtocol(Protocol):
    def initialize(self) -> None: ...

    def close(self) -> None: ...

    def save_patient(self, patient: PatientProfile) -> PatientProfile: ...

    def get_patient(self, patient_id: str) -> PatientProfile | None: ...

    def save_session(self, session: ConsultSession) -> ConsultSession: ...

    def get_session(self, session_id: str) -> ConsultSession | None: ...

    def all_sessions(self) -> Iterable[ConsultSession]: ...

    def save_documents(self, documents: Sequence[RagDocumentInput]) -> list[RagDocument]: ...

    def query_documents(self, query: str, limit: int = 5) -> list[EvidenceCitation]: ...


class InMemoryStore(StoreProtocol):
    def __init__(self) -> None:
        self.sessions: dict[str, ConsultSession] = {}
        self.patients: dict[str, PatientProfile] = {}
        self.documents: dict[str, RagDocument] = {}

    def initialize(self) -> None:
        if not self.documents:
            self.save_documents(DEFAULT_RAG_DOCUMENTS)

    def close(self) -> None:
        return None

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

    def save_documents(self, documents: Sequence[RagDocumentInput]) -> list[RagDocument]:
        saved: list[RagDocument] = []
        for item in documents:
            document = RagDocument(
                title=item.title,
                source_type=item.source_type,
                content=item.content,
                tags=item.tags,
            )
            self.documents[document.document_id] = document
            saved.append(document)
        return saved

    def query_documents(self, query: str, limit: int = 5) -> list[EvidenceCitation]:
        ranked = _rank_documents(self.documents.values(), query)
        return [_document_to_citation(document, score) for document, score in ranked[:limit]]


class PostgresRedisStore(StoreProtocol):
    SESSION_CACHE_TTL_SECONDS = 60 * 60

    def __init__(self, *, postgres_dsn: str, redis_url: str) -> None:
        self.postgres_dsn = postgres_dsn
        self.redis = Redis.from_url(redis_url, decode_responses=True)

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consult_sessions (
                    session_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            conn.commit()

        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()
            if row and int(row[0]) == 0:
                conn.commit()
                self.save_documents(DEFAULT_RAG_DOCUMENTS)

    def close(self) -> None:
        with suppress(RedisError):
            self.redis.close()

    def save_patient(self, patient: PatientProfile) -> PatientProfile:
        payload = _dump_json(patient)
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO patients (patient_id, payload, updated_at)
                VALUES (%s, %s::jsonb, %s)
                ON CONFLICT (patient_id) DO UPDATE
                SET payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (patient.patient_id, payload, now),
            )
            conn.commit()
        return patient

    def get_patient(self, patient_id: str) -> PatientProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM patients WHERE patient_id = %s",
                (patient_id,),
            ).fetchone()
        if not row:
            return None
        return PatientProfile.model_validate(_coerce_json(row[0]))

    def save_session(self, session: ConsultSession) -> ConsultSession:
        session.updated_at = utc_now()
        self.save_patient(session.patient)
        payload = _dump_json(session)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO consult_sessions (session_id, patient_id, payload, updated_at)
                VALUES (%s, %s, %s::jsonb, %s)
                ON CONFLICT (session_id) DO UPDATE
                SET patient_id = EXCLUDED.patient_id,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    session.session_id,
                    session.patient.patient_id,
                    payload,
                    session.updated_at,
                ),
            )
            conn.commit()
        self._cache_session(session)
        return session

    def get_session(self, session_id: str) -> ConsultSession | None:
        cached = self._cached_session(session_id)
        if cached is not None:
            return cached

        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM consult_sessions WHERE session_id = %s",
                (session_id,),
            ).fetchone()
        if not row:
            return None

        session = ConsultSession.model_validate(_coerce_json(row[0]))
        self._cache_session(session)
        return session

    def all_sessions(self) -> Iterable[ConsultSession]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM consult_sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [ConsultSession.model_validate(_coerce_json(row[0])) for row in rows]

    def save_documents(self, documents: Sequence[RagDocumentInput]) -> list[RagDocument]:
        saved: list[RagDocument] = []
        now = utc_now()
        with self._connect() as conn:
            for item in documents:
                document = RagDocument(
                    title=item.title,
                    source_type=item.source_type,
                    content=item.content,
                    tags=item.tags,
                    created_at=now,
                    updated_at=now,
                )
                conn.execute(
                    """
                    INSERT INTO rag_documents (
                        document_id,
                        title,
                        source_type,
                        content,
                        tags,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                    ON CONFLICT (document_id) DO UPDATE
                    SET title = EXCLUDED.title,
                        source_type = EXCLUDED.source_type,
                        content = EXCLUDED.content,
                        tags = EXCLUDED.tags,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        document.document_id,
                        document.title,
                        document.source_type,
                        document.content,
                        json.dumps(document.tags),
                        document.created_at,
                        document.updated_at,
                    ),
                )
                saved.append(document)
            conn.commit()
        return saved

    def query_documents(self, query: str, limit: int = 5) -> list[EvidenceCitation]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT document_id, title, source_type, content, tags, created_at, updated_at
                FROM rag_documents
                ORDER BY updated_at DESC
                """
            ).fetchall()

        documents = [
            RagDocument(
                document_id=row[0],
                title=row[1],
                source_type=row[2],
                content=row[3],
                tags=list(_coerce_json(row[4])),
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]
        ranked = _rank_documents(documents, query)
        return [_document_to_citation(document, score) for document, score in ranked[:limit]]

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.postgres_dsn)

    def _cache_session(self, session: ConsultSession) -> None:
        with suppress(RedisError):
            self.redis.setex(
                f"session:{session.session_id}",
                self.SESSION_CACHE_TTL_SECONDS,
                _dump_json(session),
            )

    def _cached_session(self, session_id: str) -> ConsultSession | None:
        with suppress(RedisError):
            payload = self.redis.get(f"session:{session_id}")
            if payload:
                return ConsultSession.model_validate_json(payload)
        return None


def _dump_json(model: object) -> str:
    if hasattr(model, "model_dump"):
        return json.dumps(model.model_dump(mode="json"))  # type: ignore[call-arg]
    return json.dumps(model)


def _coerce_json(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value)
    return value


def _tokenize_query(query: str) -> list[str]:
    tokens = ["".join(ch for ch in token.lower() if ch.isalnum()) for token in query.split()]
    return [token for token in tokens if token]


def _rank_documents(
    documents: Iterable[RagDocument], query: str
) -> list[tuple[RagDocument, float]]:
    lowered_query = query.lower().strip()
    tokens = _tokenize_query(query)
    ranked: list[tuple[RagDocument, float]] = []

    for document in documents:
        haystack = " ".join([document.title, document.content, *document.tags]).lower()
        score = 0.0
        if lowered_query and lowered_query in haystack:
            score += 5.0
        for token in tokens:
            score += haystack.count(token) * 1.5
        if not tokens:
            score += 1.0
        if score > 0:
            ranked.append((document, score))

    ranked.sort(key=lambda item: (item[1], item[0].updated_at), reverse=True)
    if ranked:
        return ranked
    return [(document, 1.0) for document in documents]


def _document_to_citation(document: RagDocument, score: float) -> EvidenceCitation:
    snippet = document.content[:220].rstrip()
    if len(document.content) > 220:
        snippet = f"{snippet}..."
    return EvidenceCitation(
        title=document.title,
        source_type=document.source_type,
        snippet=snippet,
        relevance=min(0.99, max(0.45, 0.45 + (score * 0.05))),
    )
