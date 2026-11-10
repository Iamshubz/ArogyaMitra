from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import require_roles
from app.api.records import _approved_worker, _can_access_patient
from app.core.config import settings
from app.db.dependencies import get_db
from app.db.models import (
    DocumentTranslation,
    FollowUpRecord,
    HealthcareContent,
    MedicalDocument,
    PatientAccessGrant,
    User,
)
from app.schemas.records import ContentResponse
from app.schemas.worker_admin import AnalyticsResponse, FollowUpCreate, FollowUpResponse, PatientSummary, SystemMonitoringResponse

worker_router = APIRouter(prefix="/worker", tags=["healthcare worker"])
admin_router = APIRouter(prefix="/admin", tags=["administration"])


@worker_router.get("/patients", response_model=list[PatientSummary])
def list_assigned_patients(
    search: Optional[str] = Query(default=None, max_length=120),
    current_user: User = Depends(require_roles("healthcare_worker")),
    db: Session = Depends(get_db),
) -> list[PatientSummary]:
    _approved_worker(current_user)
    query = (
        select(User)
        .join(PatientAccessGrant, PatientAccessGrant.patient_id == User.id)
        .options(joinedload(User.preferred_language))
        .where(PatientAccessGrant.worker_id == current_user.id, User.role == "patient")
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(User.full_name.ilike(term), User.email.ilike(term)))
    patients = db.scalars(query.order_by(User.full_name)).all()
    return [PatientSummary(id=p.id, full_name=p.full_name, email=p.email, phone_number=p.phone_number, preferred_language=p.preferred_language.code) for p in patients]


@worker_router.get("/patients/{patient_id}/translation-history")
def patient_translation_history(patient_id: int, current_user: User = Depends(require_roles("healthcare_worker")), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    _approved_worker(current_user)
    _can_access_patient(db, current_user, patient_id)
    rows = db.execute(
        select(DocumentTranslation)
        .join(MedicalDocument, MedicalDocument.id == DocumentTranslation.document_id)
        .where(MedicalDocument.patient_id == patient_id)
        .order_by(DocumentTranslation.created_at.desc())
    ).scalars().all()
    return [{"id": row.id, "document_id": row.document_id, "source_language": row.source_language, "target_language": row.target_language, "original_text": row.original_text, "translated_text": row.translated_text, "review_required": row.review_required} for row in rows]


@worker_router.post("/follow-ups", response_model=FollowUpResponse, status_code=201)
def create_follow_up(payload: FollowUpCreate, current_user: User = Depends(require_roles("healthcare_worker")), db: Session = Depends(get_db)) -> FollowUpRecord:
    _approved_worker(current_user)
    _can_access_patient(db, current_user, payload.patient_id)
    follow_up = FollowUpRecord(**payload.model_dump(), worker_id=current_user.id)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return follow_up


@worker_router.get("/follow-ups", response_model=list[FollowUpResponse])
def list_follow_ups(status: Optional[str] = Query(default=None), current_user: User = Depends(require_roles("healthcare_worker")), db: Session = Depends(get_db)) -> list[FollowUpRecord]:
    _approved_worker(current_user)
    query = select(FollowUpRecord).where(FollowUpRecord.worker_id == current_user.id)
    if status:
        query = query.where(FollowUpRecord.status == status)
    return list(db.scalars(query.order_by(FollowUpRecord.due_at)).all())


@worker_router.patch("/follow-ups/{follow_up_id}/complete", response_model=FollowUpResponse)
def complete_follow_up(follow_up_id: int, current_user: User = Depends(require_roles("healthcare_worker")), db: Session = Depends(get_db)) -> FollowUpRecord:
    _approved_worker(current_user)
    follow_up = db.get(FollowUpRecord, follow_up_id)
    if follow_up is None or follow_up.worker_id != current_user.id:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    follow_up.status = "completed"
    follow_up.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(follow_up)
    return follow_up


@admin_router.get("/analytics", response_model=AnalyticsResponse)
def analytics(current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> AnalyticsResponse:
    def count(model: type, condition=None) -> int:
        query = select(func.count()).select_from(model)
        if condition is not None:
            query = query.where(condition)
        return int(db.scalar(query) or 0)
    return AnalyticsResponse(
        users=count(User), patients=count(User, User.role == "patient"),
        healthcare_workers=count(User, User.role == "healthcare_worker"),
        active_users=count(User, User.is_active.is_(True)), documents=count(MedicalDocument),
        translations=count(DocumentTranslation), follow_ups=count(FollowUpRecord),
        published_content=count(HealthcareContent),
    )


@admin_router.get("/system", response_model=SystemMonitoringResponse)
def system_monitoring(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> SystemMonitoringResponse:
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except SQLAlchemyError:
        database_status = "unavailable"
    return SystemMonitoringResponse(api_status="ok", database_status=database_status, ai_provider="local adapter", storage_provider="supabase private storage" if settings.supabase_url else "not configured")


@admin_router.delete("/content/{content_id}", status_code=204)
def delete_content(content_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> None:
    content = db.get(HealthcareContent, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Healthcare content not found")
    db.delete(content)
    db.commit()


@admin_router.get("/content", response_model=list[ContentResponse])
def admin_content(current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[HealthcareContent]:
    return list(db.scalars(select(HealthcareContent).order_by(HealthcareContent.updated_at.desc())).all())
