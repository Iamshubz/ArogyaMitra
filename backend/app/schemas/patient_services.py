from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


ReminderStatus = Literal["scheduled", "taken", "missed", "cancelled"]


class ReminderCreate(BaseModel):
    patient_id: Optional[int] = None
    medication_name: str = Field(min_length=1, max_length=200)
    dosage: str = Field(min_length=1, max_length=120)
    instructions: str = Field(min_length=1, max_length=2000)
    scheduled_at: datetime
    end_at: Optional[datetime] = None


class ReminderResponse(ReminderCreate):
    id: int
    patient_id: int
    created_by_id: int
    status: ReminderStatus
    delivery_status: str
    taken_at: Optional[datetime]


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: int


class FacilityResponse(BaseModel):
    id: int
    name: str
    facility_type: str
    phone_number: Optional[str]
    address: str
    region: Optional[str]
    is_verified: bool


class VoiceCapabilitiesResponse(BaseModel):
    speech_recognition: bool
    speech_synthesis: bool
    supported_languages: list[str]
    fallback: str


class VoiceSynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: Literal["en", "hi", "mr"] = "en"


class VoiceSynthesisResponse(BaseModel):
    text: str
    language: str
    provider: str
    audio_available: bool
    message: str
