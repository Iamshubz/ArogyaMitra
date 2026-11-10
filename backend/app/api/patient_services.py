from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.dependencies import get_db
from app.db.models import Bookmark, EmergencyContact, HealthcareContent, HealthcareFacility, MedicationReminder, User
from app.schemas.patient_services import (
    BookmarkResponse,
    FacilityResponse,
    ReminderCreate,
    ReminderResponse,
    VoiceCapabilitiesResponse,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse,
)

router = APIRouter(tags=["patient services"])
reminder_router = APIRouter(prefix="/reminders", tags=["medication reminders"])
education_router = APIRouter(prefix="/education", tags=["health education"])
emergency_router = APIRouter(prefix="/emergency", tags=["emergency assistance"])
voice_router = APIRouter(prefix="/voice", tags=["voice assistance"])


def _reminder_response(reminder: MedicationReminder) -> ReminderResponse:
    return ReminderResponse(
        id=reminder.id,
        patient_id=reminder.patient_id,
        created_by_id=reminder.created_by_id,
        medication_name=reminder.medication_name,
        dosage=reminder.dosage,
        instructions=reminder.instructions,
        scheduled_at=reminder.scheduled_at,
        end_at=reminder.end_at,
        status=reminder.status,
        delivery_status=reminder.delivery_status,
        taken_at=reminder.taken_at,
    )


def _can_manage_reminder(reminder: MedicationReminder, current_user: User) -> None:
    if current_user.role != "admin" and reminder.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to manage this reminder")


@reminder_router.post("", response_model=ReminderResponse, status_code=201)
def create_reminder(
    payload: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    patient_id = payload.patient_id or current_user.id
    if current_user.role != "admin" and patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Patients can create reminders only for themselves")
    if payload.end_at and payload.end_at < payload.scheduled_at:
        raise HTTPException(status_code=422, detail="Reminder end time must be after its scheduled time")
    reminder = MedicationReminder(
        patient_id=patient_id,
        created_by_id=current_user.id,
        medication_name=payload.medication_name,
        dosage=payload.dosage,
        instructions=payload.instructions,
        scheduled_at=payload.scheduled_at,
        end_at=payload.end_at,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return _reminder_response(reminder)


@reminder_router.get("", response_model=list[ReminderResponse])
def list_reminders(
    include_completed: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReminderResponse]:
    query = select(MedicationReminder).where(MedicationReminder.patient_id == current_user.id)
    if not include_completed:
        query = query.where(MedicationReminder.status.in_(("scheduled", "missed")))
    reminders = db.scalars(query.order_by(MedicationReminder.scheduled_at)).all()
    return [_reminder_response(item) for item in reminders]


@reminder_router.patch("/{reminder_id}/{status}", response_model=ReminderResponse)
def update_reminder_status(
    reminder_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    if status not in {"taken", "missed", "cancelled"}:
        raise HTTPException(status_code=422, detail="Status must be taken, missed, or cancelled")
    reminder = db.get(MedicationReminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    _can_manage_reminder(reminder, current_user)
    reminder.status = status
    reminder.taken_at = datetime.now(timezone.utc) if status == "taken" else None
    db.commit()
    db.refresh(reminder)
    return _reminder_response(reminder)


@reminder_router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    reminder = db.get(MedicationReminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    _can_manage_reminder(reminder, current_user)
    db.delete(reminder)
    db.commit()


@education_router.get("/bookmarks", response_model=list[BookmarkResponse])
def list_bookmarks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Bookmark]:
    return list(db.scalars(select(Bookmark).where(Bookmark.user_id == current_user.id).order_by(Bookmark.created_at.desc())).all())


@education_router.post("/bookmarks/{content_id}", response_model=BookmarkResponse, status_code=201)
def add_bookmark(content_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Bookmark:
    if db.get(HealthcareContent, content_id) is None:
        raise HTTPException(status_code=404, detail="Healthcare content not found")
    bookmark = db.scalar(select(Bookmark).where(Bookmark.user_id == current_user.id, Bookmark.content_id == content_id))
    if bookmark is None:
        bookmark = Bookmark(user_id=current_user.id, content_id=content_id)
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
    return bookmark


@education_router.delete("/bookmarks/{content_id}", status_code=204)
def remove_bookmark(content_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    bookmark = db.scalar(select(Bookmark).where(Bookmark.user_id == current_user.id, Bookmark.content_id == content_id))
    if bookmark is not None:
        db.delete(bookmark)
        db.commit()


@emergency_router.get("/contacts")
def emergency_contacts(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    contacts = db.scalars(select(EmergencyContact).where(EmergencyContact.is_verified)).all()
    return [{"id": item.id, "name": item.name, "phone_number": item.phone_number, "region": item.region, "is_verified": item.is_verified} for item in contacts]


@emergency_router.get("/facilities", response_model=list[FacilityResponse])
def emergency_facilities(region: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> list[HealthcareFacility]:
    query = select(HealthcareFacility).where(HealthcareFacility.is_verified)
    if region:
        query = query.where(HealthcareFacility.region == region)
    return list(db.scalars(query.order_by(HealthcareFacility.name)).all())


@voice_router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
def voice_capabilities() -> VoiceCapabilitiesResponse:
    return VoiceCapabilitiesResponse(
        speech_recognition=True,
        speech_synthesis=True,
        supported_languages=["en-IN", "hi-IN", "mr-IN"],
        fallback="If your browser does not support voice, use the editable text assistant.",
    )


@voice_router.post("/synthesize", response_model=VoiceSynthesisResponse)
def synthesize_voice(payload: VoiceSynthesisRequest, current_user: User = Depends(require_roles("patient", "healthcare_worker", "admin"))) -> VoiceSynthesisResponse:
    return VoiceSynthesisResponse(
        text=payload.text,
        language=payload.language,
        provider="browser",
        audio_available=False,
        message="Use the browser SpeechSynthesis API to play this text. No audio was uploaded or generated by the server.",
    )
