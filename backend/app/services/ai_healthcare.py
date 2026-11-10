from __future__ import annotations

import re
from dataclasses import dataclass


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
