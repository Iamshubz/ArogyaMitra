from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionCreate(BaseModel):
    patient_id: int
    medication_name: str = Field(min_length=1, max_length=200)
    dosage: str = Field(min_length=1, max_length=120)
    instructions: str = Field(min_length=1, max_length=2000)
    prescription_date: date
    document_id: Optional[int] = None


class PrescriptionResponse(PrescriptionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    healthcare_worker_id: int


class MedicalReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    title: str
    report_type: str
    report_date: date
    description: Optional[str]
    document_id: int

class DischargeSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    discharge_date: date
    facility_name: Optional[str]
    document_id: int

class ContentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    category: str = Field(min_length=1, max_length=80)
    language_code: str = Field(min_length=2, max_length=10)
    body: str = Field(min_length=1)
    publication_date: date


class ContentResponse(ContentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_id: int
