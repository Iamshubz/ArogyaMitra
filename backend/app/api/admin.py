from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.dependencies import get_db
from app.db.models import PatientAccessGrant, User

router = APIRouter(prefix="/admin", tags=["administration"])


@router.post("/healthcare-workers/{user_id}/approve")
def approve_worker(user_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict[str, str]:
    worker = db.get(User, user_id)
    if worker is None or worker.role != "healthcare_worker" or worker.worker_profile is None:
        raise HTTPException(status_code=404, detail="Healthcare worker not found")
    worker.worker_profile.is_approved = True
    db.commit()
    return {"status": "approved"}


@router.post("/patient-access/{patient_id}/workers/{worker_id}")
def grant_patient_access(
    patient_id: int,
    worker_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    patient = db.get(User, patient_id)
    worker = db.get(User, worker_id)
    if patient is None or patient.role != "patient" or worker is None or worker.role != "healthcare_worker":
        raise HTTPException(status_code=404, detail="Patient or healthcare worker not found")
    existing = db.scalar(select(PatientAccessGrant).where(
        PatientAccessGrant.patient_id == patient_id,
        PatientAccessGrant.worker_id == worker_id,
    ))
    if existing is None:
        db.add(PatientAccessGrant(patient_id=patient_id, worker_id=worker_id))
        db.commit()
    return {"status": "granted"}
