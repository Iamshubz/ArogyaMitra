from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.security import hash_password
from app.db.models import LanguagePreference, User
from tests.test_auth import TestingSessionLocal, client


def _register(role: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Phase 5 {role}",
            "email": f"phase5-{role}-{uuid4().hex}@example.com",
            "password": "secure-password",
            "preferred_language": "en",
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_worker_and_admin_routes_enforce_roles():
    patient = _register("patient")
    patient_headers = {"Authorization": f"Bearer {patient['access_token']}"}
    assert client.get("/api/v1/worker/patients", headers=patient_headers).status_code == 403
    assert client.get("/api/v1/admin/analytics", headers=patient_headers).status_code == 403


def test_worker_follow_up_requires_approved_access():
    worker = _register("healthcare_worker")
    patient = _register("patient")
    response = client.post(
        "/api/v1/worker/follow-ups",
        headers={"Authorization": f"Bearer {worker['access_token']}"},
        json={
            "patient_id": patient["user"]["id"],
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "notes": "Review follow-up",
        },
    )
    assert response.status_code == 403


def test_approved_worker_follow_up_and_admin_monitoring_persist():
    worker = _register("healthcare_worker")
    patient = _register("patient")
    with TestingSessionLocal() as db:
        language = db.query(LanguagePreference).filter_by(code="en").first()
        admin = User(
            full_name="Phase 5 Admin",
            email=f"admin-{uuid4().hex}@example.com",
            password_hash=hash_password("secure-password"),
            role="admin",
            preferred_language_id=language.id,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id
        worker_id = worker["user"]["id"]
        patient_id = patient["user"]["id"]
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "secure-password"},
    )
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    assert client.post(f"/api/v1/admin/healthcare-workers/{worker_id}/approve", headers=admin_headers).status_code == 200
    assert client.post(f"/api/v1/admin/patient-access/{patient_id}/workers/{worker_id}", headers=admin_headers).status_code == 200

    follow_up = client.post(
        "/api/v1/worker/follow-ups",
        headers={"Authorization": f"Bearer {worker['access_token']}"},
        json={
            "patient_id": patient_id,
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "notes": "Review follow-up",
        },
    )
    assert follow_up.status_code == 201
    follow_up_id = follow_up.json()["id"]
    complete = client.patch(
        f"/api/v1/worker/follow-ups/{follow_up_id}/complete",
        headers={"Authorization": f"Bearer {worker['access_token']}"},
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    analytics = client.get("/api/v1/admin/analytics", headers=admin_headers)
    assert analytics.status_code == 200
    assert analytics.json()["follow_ups"] >= 1
    system = client.get("/api/v1/admin/system", headers=admin_headers)
    assert system.status_code == 200
    assert system.json()["database_status"] == "connected"
