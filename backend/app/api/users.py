from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_user_response
from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.db.models import HealthcareWorkerProfile, LanguagePreference, PatientProfile, User
from app.schemas.auth import ProfileUpdateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    return get_user_response(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    language = db.scalar(
        select(LanguagePreference).where(LanguagePreference.code == payload.preferred_language)
    )
    if language is None:
        raise HTTPException(status_code=422, detail="Unsupported preferred language")
    current_user.full_name = payload.full_name.strip()
    current_user.phone_number = payload.phone_number
    current_user.preferred_language_id = language.id
    if current_user.role == "patient":
        if current_user.patient_profile is None:
            current_user.patient_profile = PatientProfile()
        current_user.patient_profile.age = payload.age
        current_user.patient_profile.date_of_birth = payload.date_of_birth
        current_user.patient_profile.gender = payload.gender
        current_user.patient_profile.address = payload.address
    elif current_user.role == "healthcare_worker":
        if current_user.worker_profile is None:
            current_user.worker_profile = HealthcareWorkerProfile()
        current_user.worker_profile.facility_name = payload.facility_name
        current_user.worker_profile.specialization = payload.specialization
        current_user.worker_profile.designation = payload.designation
        current_user.worker_profile.address = payload.address
    db.commit()
    refreshed = db.scalar(
        select(User)
        .options(
            joinedload(User.preferred_language),
            joinedload(User.patient_profile),
            joinedload(User.worker_profile),
        )
        .where(User.id == current_user.id)
    )
    if refreshed is None:
        raise RuntimeError("Updated account could not be loaded")
    return get_user_response(refreshed)
