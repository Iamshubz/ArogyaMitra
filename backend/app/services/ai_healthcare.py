from __future__ import annotations

import re
from typing import Any
import httpx
from dataclasses import dataclass

from app.core.config import settings


DISCLAIMER = (
    "Information support only. This result is not a diagnosis or prescription. "
    "Confirm medical information with a qualified healthcare professional."
)

_TRANSLATIONS = {
    ("en", "hi"): {
        "take": "लेना",
        "once daily": "दिन में एक बार",
        "twice daily": "दिन में दो बार",
        "after food": "खाने के बाद",
        "before food": "खाने से पहले",
        "fever": "बुखार",
        "high blood pressure": "उच्च रक्तचाप",
    },
    ("en", "mr"): {
        "take": "घ्या",
        "once daily": "दिवसातून एकदा",
        "twice daily": "दिवसातून दोनदा",
        "after food": "जेवणानंतर",
        "before food": "जेवणापूर्वी",
        "fever": "ताप",
        "high blood pressure": "उच्च रक्तदाब",
    },
}

_SIMPLIFICATIONS = {
    "hypertension": "High blood pressure. It means blood pushes against blood vessel walls more than usual.",
    "diabetes": "A condition where blood sugar stays higher than the body can safely manage.",
    "inflammation": "Swelling and irritation in part of the body, often causing pain or warmth.",
    "dehydration": "Not having enough water in the body.",
}

_MEDICINES = {"paracetamol", "acetaminophen", "amoxicillin", "metformin", "ibuprofen"}
_SYMPTOMS = {"fever", "cough", "headache", "pain", "vomiting", "diarrhea", "breathing difficulty"}
_DOSAGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|tablet|tablets|capsule|capsules)\b", re.I)


def _openai_request(messages: list[dict[str, Any]], image: str | None = None) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("AI service is not configured. Set OPENAI_API_KEY in backend/.env.")
    if image is not None:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": messages[0]["content"]},
                    {"type": "image_url", "image_url": {"url": image}},
                ],
            }
        ]
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_model, "messages": messages, "temperature": 0.2},
            timeout=45,
        )
        response.raise_for_status()
        body = response.json()
        answer = body["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("The AI provider could not process this request.") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("The AI provider returned an empty response.")
    return answer.strip()


def chat_with_patient(message: str, language: str) -> str:
    return _openai_request([{
        "role": "system",
        "content": (
            "You are ArogyaMitra, a cautious healthcare information assistant. "
            "Answer in the requested language when possible. Do not diagnose, prescribe, "
            "or tell the patient to change medication. Encourage a clinician for personal "
            "medical decisions and emergency services for urgent symptoms. "
            f"Requested language: {language}."
        ),
    }, {"role": "user", "content": message}])


def analyze_medical_image(content_type: str, content: bytes, language: str) -> str:
    import base64

    encoded = base64.b64encode(content).decode("ascii")
    prompt = (
        "Read this medical image (prescription, label, or report) and explain only what is "
        "clearly visible in simple language. Transcribe important text, medicines, dosage, "
        "and dates when legible. Mark uncertain text as uncertain. Never invent missing "
        f"details and do not diagnose or prescribe. Respond in {language}."
    )
    return _openai_request([{"role": "user", "content": prompt}], f"data:{content_type};base64,{encoded}")


def translate_text(text: str, source: str, target: str) -> str:
    if source == target:
        return text
    translated = text
    for phrase, replacement in _TRANSLATIONS.get((source, target), {}).items():
        translated = re.sub(re.escape(phrase), replacement, translated, flags=re.I)
    return translated


def simplify_text(text: str, target: str) -> str:
    simplified = text
    for term, explanation in _SIMPLIFICATIONS.items():
        if re.search(rf"\b{re.escape(term)}\b", simplified, flags=re.I):
            simplified = re.sub(rf"\b{re.escape(term)}\b", explanation, simplified, flags=re.I)
    if target != "en":
        simplified = translate_text(simplified, "en", target)
    return simplified


def extract_entities(text: str) -> list[dict[str, str | bool]]:
    lowered = text.lower()
    entities: list[dict[str, str | bool]] = []
    for medicine in sorted(_MEDICINES):
        if re.search(rf"\b{re.escape(medicine)}\b", lowered):
            entities.append({"entity_type": "medicine", "value": medicine, "confidence": "medium", "review_required": True})
    for symptom in sorted(_SYMPTOMS):
        if re.search(rf"\b{re.escape(symptom)}\b", lowered):
            entities.append({"entity_type": "symptom", "value": symptom, "confidence": "low", "review_required": True})
    for dosage in _DOSAGE_PATTERN.findall(text):
        entities.append({"entity_type": "dosage", "value": dosage, "confidence": "medium", "review_required": True})
    return entities


@dataclass(frozen=True)
class SymptomGuidance:
    overview: str
    self_care: list[str]
    warning_signs: list[str]
    seek_care: str
    emergency: bool


def symptom_guidance(symptom: str, severity: str | None) -> SymptomGuidance:
    normalized = symptom.strip().lower()
    emergency = severity == "severe" or normalized in {"breathing difficulty", "chest pain"}
    if emergency:
        return SymptomGuidance(
            overview="Severe symptoms can require urgent assessment.",
            self_care=["Contact emergency services now; do not delay care for online guidance."],
            warning_signs=["Trouble breathing, fainting, blue lips, confusion, or severe chest pain."],
            seek_care="Call India's emergency number 112 or your local emergency service immediately.",
            emergency=True,
        )
    return SymptomGuidance(
        overview=f"{symptom.strip().capitalize()} can have many causes and cannot be diagnosed here.",
        self_care=["Rest and drink suitable fluids if you can do so safely.", "Track when the symptom started and whether it is changing."],
        warning_signs=["Symptoms that rapidly worsen, persist, or occur with severe pain, confusion, or difficulty breathing."],
        seek_care="Contact a healthcare professional if symptoms persist, worsen, or concern you.",
        emergency=False,
    )
