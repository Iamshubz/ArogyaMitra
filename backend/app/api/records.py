from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.core.storage import StorageNotConfigured, download_private, upload_private
from app.db.dependencies import get_db
from app.db.models import (
    DischargeSummary,
    HealthcareContent,
    MedicalDocument,
    MedicalReport,
    PatientAccessGrant,
    Prescription,
    User,
)
from app.schemas.records import (
    ContentCreate,
    ContentResponse,
    DischargeSummaryResponse,
    MedicalReportResponse,
    PrescriptionCreate,
    PrescriptionResponse,
)

router = APIRouter(prefix="/records", tags=["healthcare records"])
content_router = APIRouter(prefix="/content", tags=["healthcare content"])
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def _approved_worker(user: User) -> None:
    if user.role != "healthcare_worker" or not user.worker_profile or not user.worker_profile.is_approved:
        raise HTTPException(status_code=403, detail="An approved healthcare worker account is required")


def _can_access_patient(db: Session, current_user: User, patient_id: int) -> None:
    if current_user.role == "patient" and current_user.id == patient_id:
        return
    if current_user.role == "healthcare_worker":
        _approved_worker(current_user)
        if db.scalar(select(PatientAccessGrant.id).where(
            PatientAccessGrant.worker_id == current_user.id,
            PatientAccessGrant.patient_id == patient_id,
        )) is not None:
            return
    if current_user.role == "admin":
        return
    raise HTTPException(status_code=403, detail="You are not authorized to access this patient's records")


async def _store_upload(file: UploadFile, patient_id: int, document_type: str) -> MedicalDocument:
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_TYPES or suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF, JPG, JPEG, and PNG files are supported")
    content = await file.read(settings.max_upload_size + 1)
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File exceeds the upload size limit")
    path = f"{patient_id}/{uuid4().hex}{suffix}"
    try:
        upload_private(path, content, file.content_type)
    except (StorageNotConfigured, httpx.HTTPError) as exc:
        raise HTTPException(status_code=503, detail="Private document storage is unavailable") from exc
    return MedicalDocument(
        patient_id=patient_id,
        uploaded_by_id=0,
        document_type=document_type,
        title=file.filename or "Medical document",
        original_filename=file.filename or "document",
        storage_path=path,
        content_type=file.content_type,
        file_size=len(content),
    )


@router.post("/prescriptions", response_model=PrescriptionResponse, status_code=201)
def create_prescription(
    payload: PrescriptionCreate,
    current_user: User = Depends(require_roles("healthcare_worker")),
    db: Session = Depends(get_db),
) -> Prescription:
    _approved_worker(current_user)
    _can_access_patient(db, current_user, payload.patient_id)
    prescription = Prescription(**payload.model_dump(), healthcare_worker_id=current_user.id)
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@router.get("/prescriptions", response_model=list[PrescriptionResponse])
def list_prescriptions(
    patient_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Prescription]:
    target = patient_id or current_user.id
    _can_access_patient(db, current_user, target)
    return list(db.scalars(select(Prescription).where(Prescription.patient_id == target).order_by(Prescription.prescription_date.desc())).all())


@router.post("/documents", status_code=201)
async def upload_document(
    patient_id: int = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(default=None),
    document_date: Optional[date] = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role == "patient" and patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Patients can upload only their own documents")
    if current_user.role == "healthcare_worker":
        _can_access_patient(db, current_user, patient_id)
    elif current_user.role not in {"patient", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    document = await _store_upload(file, patient_id, document_type)
    document.uploaded_by_id = current_user.id
    document.title = title
    document.description = description
    document.document_date = document_date
    db.add(document)
    db.commit()
    db.refresh(document)
    return {"id": document.id, "title": document.title, "document_type": document.document_type, "file_size": document.file_size}


@router.get("/documents")
def list_documents(
    patient_id: Optional[int] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    target = patient_id or current_user.id
    _can_access_patient(db, current_user, target)
    query = select(MedicalDocument).where(MedicalDocument.patient_id == target)
    if document_type:
        query = query.where(MedicalDocument.document_type == document_type)
    if start_date:
        query = query.where(MedicalDocument.document_date >= start_date)
    if end_date:
        query = query.where(MedicalDocument.document_date <= end_date)
    query = query.order_by(MedicalDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    documents = list(db.scalars(query).all())
    return {"page": page, "page_size": page_size, "items": [
        {"id": item.id, "patient_id": item.patient_id, "document_type": item.document_type, "title": item.title,
         "description": item.description, "original_filename": item.original_filename, "content_type": item.content_type,
         "file_size": item.file_size, "document_date": item.document_date, "created_at": item.created_at}
        for item in documents
    ]}


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    document = db.get(MedicalDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    _can_access_patient(db, current_user, document.patient_id)
    try:
        stored = download_private(document.storage_path)
    except (StorageNotConfigured, httpx.HTTPError) as exc:
        raise HTTPException(status_code=503, detail="Private document storage is unavailable") from exc
    return Response(content=stored.content, media_type=document.content_type, headers={
        "Content-Disposition": f'attachment; filename="{document.original_filename}"'
    })


@router.post("/reports", response_model=MedicalReportResponse, status_code=201)
async def create_report(
    patient_id: int = Form(...), title: str = Form(...), report_type: str = Form(...),
    report_date: date = Form(...), description: Optional[str] = Form(default=None),
    file: UploadFile = File(...), current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalReport:
    if current_user.role == "healthcare_worker":
        _can_access_patient(db, current_user, patient_id)
    elif current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="You can create reports only for yourself")
    document = await _store_upload(file, patient_id, "medical_report")
    document.uploaded_by_id = current_user.id
    document.title = title
    document.description = description
    document.document_date = report_date
    db.add(document)
    db.flush()
    report = MedicalReport(
        patient_id=patient_id, uploaded_by_id=current_user.id, document_id=document.id,
        title=title, report_type=report_type, report_date=report_date, description=description,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=list[MedicalReportResponse])
def list_reports(patient_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MedicalReport]:
    target = patient_id or current_user.id
    _can_access_patient(db, current_user, target)
    return list(db.scalars(select(MedicalReport).where(MedicalReport.patient_id == target).order_by(MedicalReport.report_date.desc())).all())


@router.post("/discharge-summaries", response_model=DischargeSummaryResponse, status_code=201)
async def create_discharge_summary(
    patient_id: int = Form(...), discharge_date: date = Form(...),
    facility_name: Optional[str] = Form(default=None), file: UploadFile = File(...),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
) -> DischargeSummary:
    if current_user.role == "healthcare_worker":
        _can_access_patient(db, current_user, patient_id)
    elif current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="You can create summaries only for yourself")
    document = await _store_upload(file, patient_id, "discharge_summary")
    document.uploaded_by_id = current_user.id
    document.title = "Discharge summary"
    document.document_date = discharge_date
    db.add(document)
    db.flush()
    summary = DischargeSummary(
        patient_id=patient_id, uploaded_by_id=current_user.id, document_id=document.id,
        discharge_date=discharge_date, facility_name=facility_name,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@router.get("/discharge-summaries", response_model=list[DischargeSummaryResponse])
def list_discharge_summaries(patient_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DischargeSummary]:
    target = patient_id or current_user.id
    _can_access_patient(db, current_user, target)
    return list(db.scalars(select(DischargeSummary).where(DischargeSummary.patient_id == target).order_by(DischargeSummary.discharge_date.desc())).all())


@content_router.get("", response_model=list[ContentResponse])
def list_content(language_code: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)) -> list[HealthcareContent]:
    query = select(HealthcareContent).order_by(HealthcareContent.publication_date.desc())
    if language_code:
        query = query.where(HealthcareContent.language_code == language_code)
    if category:
        query = query.where(HealthcareContent.category == category)
    return list(db.scalars(query).all())


@content_router.get("/{content_id}", response_model=ContentResponse)
def get_content(content_id: int, db: Session = Depends(get_db)) -> HealthcareContent:
    content = db.get(HealthcareContent, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Healthcare content not found")
    return content


@content_router.post("", response_model=ContentResponse, status_code=201)
def create_content(payload: ContentCreate, current_user: User = Depends(require_roles("healthcare_worker", "admin")), db: Session = Depends(get_db)) -> HealthcareContent:
    if current_user.role == "healthcare_worker":
        _approved_worker(current_user)
    content = HealthcareContent(**payload.model_dump(), author_id=current_user.id)
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@content_router.put("/{content_id}", response_model=ContentResponse)
def update_content(content_id: int, payload: ContentCreate, current_user: User = Depends(require_roles("healthcare_worker", "admin")), db: Session = Depends(get_db)) -> HealthcareContent:
    content = db.get(HealthcareContent, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Healthcare content not found")
    if current_user.role == "healthcare_worker":
        _approved_worker(current_user)
        if content.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="You may edit only content you created")
    for key, value in payload.model_dump().items():
        setattr(content, key, value)
    db.commit()
    db.refresh(content)
    return content
