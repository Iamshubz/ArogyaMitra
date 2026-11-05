from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.dependencies import get_db
from app.db.models import HealthcareWorkerProfile, LanguagePreference, PatientProfile, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_user_response(user: User) -> UserResponse:
    age = user.patient_profile.age if user.patient_profile else None
    facility_name = user.worker_profile.facility_name if user.worker_profile else None
    specialization = user.worker_profile.specialization if user.worker_profile else None
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        preferred_language=user.preferred_language,
        age=age,
        facility_name=facility_name,
        specialization=specialization,
    )


def load_user(db: Session, user_id: int) -> Optional[User]:
    return db.scalar(
        select(User)
        .options(
            joinedload(User.preferred_language),
            joinedload(User.patient_profile),
            joinedload(User.worker_profile),
        )
        .where(User.id == user_id)
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    language = db.scalar(
        select(LanguagePreference).where(LanguagePreference.code == payload.preferred_language)
    )
    if language is None:
        language = LanguagePreference(
            code=payload.preferred_language,
            name=payload.preferred_language.upper(),
        )
        db.add(language)
        db.flush()

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        phone_number=payload.phone_number,
        role=payload.role,
        preferred_language_id=language.id,
    )
    db.add(user)
    db.flush()
    if payload.role == "patient":
        db.add(PatientProfile(user_id=user.id, age=payload.age))
    else:
        db.add(HealthcareWorkerProfile(user_id=user.id))
    db.commit()
    user = load_user(db, user.id)
    if user is None:
        raise HTTPException(status_code=500, detail="Unable to load the created account")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=get_user_response(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(
            joinedload(User.preferred_language),
            joinedload(User.patient_profile),
            joinedload(User.worker_profile),
        )
        .where(User.email == payload.email.lower())
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=get_user_response(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return get_user_response(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    return None
