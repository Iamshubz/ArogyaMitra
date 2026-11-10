from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tests.test_auth import client


def _token() -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Reminder Patient",
            "email": f"reminder-{uuid4().hex}@example.com",
            "password": "secure-password",
            "preferred_language": "en",
            "role": "patient",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_reminder_persists_and_can_be_marked_taken():
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/reminders",
        headers=headers,
        json={
            "medication_name": "Prescribed medicine",
            "dosage": "500 mg",
            "instructions": "Take after food",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
    )
    assert response.status_code == 201
    reminder_id = response.json()["id"]
    assert response.json()["delivery_status"] == "not_sent"

    updated = client.patch(f"/api/v1/reminders/{reminder_id}/taken", headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "taken"
    assert updated.json()["taken_at"] is not None


def test_reminder_rejects_invalid_end_time():
    token = _token()
    response = client.post(
        "/api/v1/reminders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "medication_name": "Medicine",
            "dosage": "1 tablet",
            "instructions": "Follow prescription",
            "scheduled_at": "2026-11-10T10:00:00+00:00",
            "end_at": "2026-11-10T09:00:00+00:00",
        },
    )
    assert response.status_code == 422


def test_voice_and_emergency_endpoints_are_explicit():
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    voice = client.get("/api/v1/voice/capabilities")
    assert voice.status_code == 200
    assert "hi-IN" in voice.json()["supported_languages"]
    emergency = client.get("/api/v1/emergency/contacts")
    assert emergency.status_code == 200
