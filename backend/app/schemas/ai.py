from __future__ import annotations

from typing import Dict, Literal, Optional, Union

from pydantic import BaseModel, Field


LanguageCode = Literal["en", "hi", "mr"]


class TextProcessingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    source_language: LanguageCode = "en"
    target_language: LanguageCode = "en"
    document_id: Optional[int] = None


class TranslationResponse(BaseModel):
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    review_required: bool = True
    disclaimer: str


class SimplificationResponse(BaseModel):
    original_text: str
    simplified_text: str
    target_language: str
    disclaimer: str


class MedicalEntity(BaseModel):
    entity_type: str
    value: str
    context: Optional[str] = None
    confidence: Literal["low", "medium", "high"]
    review_required: bool = True


class ExtractionResponse(BaseModel):
    entities: list[MedicalEntity]
    review_required: bool = True
    disclaimer: str


class SymptomRequest(BaseModel):
    symptom: str = Field(min_length=2, max_length=120)
    duration: Optional[str] = Field(default=None, max_length=80)
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    language: LanguageCode = "en"


class SymptomResponse(BaseModel):
    symptom: str
    overview: str
    self_care: list[str]
    warning_signs: list[str]
    seek_care: str
    emergency: bool
    disclaimer: str


class RecommendationResponse(BaseModel):
    items: list[Dict[str, Union[str, int]]]
    reason: str
    disclaimer: str
