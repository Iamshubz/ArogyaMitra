from __future__ import annotations

from uuid import uuid4

from tests.test_auth import client


def _token() -> str:
    email = f"ai-{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "AI Test Patient",
            "email": email,
            "password": "secure-password",
            "preferred_language": "en",
            "role": "patient",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_translation_preserves_original_and_requires_review():
    token = _token()
    response = client.post(
        "/api/v1/ai/translation",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Take paracetamol once daily after food",
            "source_language": "en",
            "target_language": "hi",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["original_text"] == "Take paracetamol once daily after food"
    assert body["review_required"] is True
    assert "paracetamol" in body["translated_text"]


def test_extraction_marks_entities_for_review():
    token = _token()
    response = client.post(
        "/api/v1/ai/extract",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Paracetamol 500 mg for fever", "source_language": "en"},
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(entity["entity_type"] == "medicine" for entity in entities)
    assert all(entity["review_required"] is True for entity in entities)


def test_severe_symptom_escalates_to_emergency_services():
    token = _token()
    response = client.post(
        "/api/v1/ai/symptoms",
        headers={"Authorization": f"Bearer {token}"},
        json={"symptom": "chest pain", "severity": "severe", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["emergency"] is True
    assert "112" in body["seek_care"]


def test_ai_endpoints_require_authentication():
    response = client.post(
        "/api/v1/ai/simplification",
        json={"text": "hypertension", "source_language": "en", "target_language": "en"},
    )
    assert response.status_code == 401
