import os

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app

os.environ["MEDDASH_STORE_MODE"] = "inmemory"


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_consult_flow_and_events(client: TestClient) -> None:
    start_response = client.post(
        "/api/consult/start",
        json={
            "patient": {
                "full_name": "Alice Doe",
                "age": 42,
                "allergies": ["penicillin"],
            },
            "opening_message": "I have chest pain and shortness of breath.",
        },
    )
    session = start_response.json()
    session_id = session["session_id"]

    assert start_response.status_code == 200
    assert session["triage"]["handoff_required"] is True

    chat_response = client.post(
        "/api/consult/chat",
        params={"session_id": session_id},
        json={"message": "I am allergic to penicillin and was prescribed amoxicillin."},
    )

    assert chat_response.status_code == 200
    updated = chat_response.json()
    assert updated["status"] == "needs_handoff"
    assert updated["patient"]["allergies"] == ["penicillin"]
    assert updated["triage"]["urgency"] == "critical"
    assert len(updated["medication_alerts"]) >= 1

    event_response = client.get(f"/api/consult/{session_id}/events")

    assert event_response.status_code == 200
    assert "event: workflow.step" in event_response.text


def test_supporting_endpoints(client: TestClient) -> None:
    patient_response = client.post(
        "/api/patient/save",
        json={"patient": {"full_name": "Bob Smith", "age": 30}},
    )
    assert patient_response.status_code == 200

    document_response = client.post(
        "/api/rag/documents",
        json={
            "documents": [
                {
                    "title": "Community-acquired pneumonia note",
                    "source_type": "guideline",
                    "content": "Chest imaging is recommended when pneumonia symptoms escalate.",
                    "tags": ["pneumonia", "imaging"],
                }
            ]
        },
    )
    assert document_response.status_code == 200
    assert document_response.json()["documents"]

    rag_response = client.post("/api/rag/query", json={"query": "fever and cough"})
    assert rag_response.status_code == 200
    assert len(rag_response.json()["citations"]) == 2

    diagnosis_response = client.post(
        "/api/diagnosis/generate",
        json={"symptoms": ["fever", "cough"], "notes": "viral symptoms"},
    )
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["differential"]
