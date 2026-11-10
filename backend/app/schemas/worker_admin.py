from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PatientSummary(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: Optional[str]
    preferred_language: str


class FollowUpCreate(BaseModel):
    patient_id: int
    due_at: datetime
    notes: str = Field(min_length=1, max_length=2000)


class FollowUpResponse(FollowUpCreate):
    id: int
    worker_id: int
    status: Literal["scheduled", "completed", "missed"]
    completed_at: Optional[datetime]


class AnalyticsResponse(BaseModel):
    users: int
    patients: int
    healthcare_workers: int
    active_users: int
    documents: int
    translations: int
    follow_ups: int
    published_content: int


class SystemMonitoringResponse(BaseModel):
    api_status: str
    database_status: str
    ai_provider: str
    storage_provider: str
