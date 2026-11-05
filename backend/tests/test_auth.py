import os

os.environ["DATABASE_URL"] = "sqlite:///./test_arogyamitra.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.dependencies import get_db
from app.db.models import LanguagePreference
from app.db.session import Base
from app.main import app

engine = create_engine("sqlite:///./test_arogyamitra.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)
with TestingSessionLocal() as db:
    if db.query(LanguagePreference).filter_by(code="en").first() is None:
        db.add(LanguagePreference(code="en", name="English"))
        db.commit()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_register_login_and_profile():
    email = "test.patient@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Patient",
            "email": email,
            "password": "secure-password",
            "phone_number": "9876543210",
            "age": 29,
            "preferred_language": "en",
            "role": "patient",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    assert response.json()["user"]["role"] == "patient"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secure-password"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200
    assert profile.json()["age"] == 29


def test_invalid_login_is_rejected():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
