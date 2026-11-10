from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.records import _can_access_patient
from app.db.dependencies import get_db
from app.db.models import (
    AIProcessingLog,
    DocumentTranslation,
    ExtractedMedicalEntity,
    HealthcareContent,
    MedicalDocument,
    User,
)
from app.schemas.ai import (
    ExtractionResponse,
    RecommendationResponse,
    SimplificationResponse,
    SymptomRequest,
    SymptomResponse,
    TextProcessingRequest,
    TranslationResponse,
)
from app.services.ai_healthcare import DISCLAIMER, extract_entities, simplify_text, symptom_guidance, translate_text

router = APIRouter(prefix="/ai", tags=["AI healthcare assistance"])


def _document_for_user(document_id: int, current_user: User, db: Session) -> MedicalDocument:
    document = db.get(MedicalDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Medical document not found")
    _can_access_patient(db, current_user, document.patient_id)
    return document


def _log(db: Session, user_id: int, operation: str, source: str | None = None, target: str | None = None) -> None:
    db.add(AIProcessingLog(
        user_id=user_id,
        operation=operation,
        input_language=source,
        output_language=target,
        provider="local",
        status="completed",
    ))


@router.post("/translation", response_model=TranslationResponse)
def translate(
    payload: TextProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TranslationResponse:
    if payload.document_id is not None:
        document = _document_for_user(payload.document_id, current_user, db)
    translated = translate_text(payload.text, payload.source_language, payload.target_language)
    if payload.document_id is not None:
        db.add(DocumentTranslation(
            document_id=document.id,
            created_by_id=current_user.id,
            source_language=payload.source_language,
            target_language=payload.target_language,
            original_text=payload.text,
            translated_text=translated,
        ))
    _log(db, current_user.id, "translation", payload.source_language, payload.target_language)
    db.commit()
    return TranslationResponse(
        source_language=payload.source_language,
        target_language=payload.target_language,
        original_text=payload.text,
        translated_text=translated,
        disclaimer=DISCLAIMER,
    )


@router.post("/simplification", response_model=SimplificationResponse)
def simplify(
    payload: TextProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SimplificationResponse:
    if payload.document_id is not None:
        _document_for_user(payload.document_id, current_user, db)
    simplified = simplify_text(payload.text, payload.target_language)
    _log(db, current_user.id, "simplification", payload.source_language, payload.target_language)
    db.commit()
    return SimplificationResponse(
        original_text=payload.text,
        simplified_text=simplified,
        target_language=payload.target_language,
        disclaimer=DISCLAIMER,
    )


@router.post("/extract", response_model=ExtractionResponse)
def extract(
    payload: TextProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractionResponse:
    document = _document_for_user(payload.document_id, current_user, db) if payload.document_id is not None else None
    entities = extract_entities(payload.text)
    if document is not None:
        for entity in entities:
            db.add(ExtractedMedicalEntity(
                document_id=document.id,
                created_by_id=current_user.id,
                entity_type=str(entity["entity_type"]),
                value=str(entity["value"]),
                confidence=str(entity["confidence"]),
                review_required=True,
            ))
    _log(db, current_user.id, "entity_extraction", payload.source_language)
    db.commit()
    return ExtractionResponse(entities=entities, disclaimer=DISCLAIMER)


@router.post("/symptoms", response_model=SymptomResponse)
def symptoms(payload: SymptomRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SymptomResponse:
    guidance = symptom_guidance(payload.symptom, payload.severity)
    _log(db, current_user.id, "symptom_guidance", payload.language)
    db.commit()
    return SymptomResponse(
        symptom=payload.symptom,
        overview=guidance.overview,
        self_care=guidance.self_care,
        warning_signs=guidance.warning_signs,
        seek_care=guidance.seek_care,
        emergency=guidance.emergency,
        disclaimer=DISCLAIMER,
    )


@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RecommendationResponse:
    language = current_user.preferred_language.code
    query = (
        select(HealthcareContent)
        .where(HealthcareContent.language_code == language)
        .order_by(HealthcareContent.publication_date.desc())
        .limit(5)
    )
    content = list(db.scalars(query).all())
    if not content and language != "en":
        content = list(db.scalars(
            select(HealthcareContent)
            .where(HealthcareContent.language_code == "en")
            .order_by(HealthcareContent.publication_date.desc())
            .limit(5)
        ).all())
    return RecommendationResponse(
        items=[{"id": item.id, "title": item.title, "category": item.category, "language_code": item.language_code} for item in content],
        reason="Recommendations are based only on your language preference and published health education content.",
        disclaimer=DISCLAIMER,
    )
