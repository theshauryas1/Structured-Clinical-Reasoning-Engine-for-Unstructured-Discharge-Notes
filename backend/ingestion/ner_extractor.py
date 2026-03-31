import re
from typing import Dict, List, Tuple

import spacy

CLINICAL_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(left-sided weakness|right-sided weakness|weakness)\b", "SYMPTOM"),
    (r"\b(expressive aphasia|aphasia)\b", "SYMPTOM"),
    (r"\b(facial droop)\b", "SYMPTOM"),
    (r"\b(blurry vision|vision changes)\b", "SYMPTOM"),
    (r"\b(shortness of breath|sob)\b", "SYMPTOM"),
    (r"\b(productive cough|cough)\b", "SYMPTOM"),
    (r"\b(fever|febrile)\b", "SYMPTOM"),
    (r"\b(chest pain)\b", "SYMPTOM"),
    (r"\b(palpitations)\b", "SYMPTOM"),
    (r"\b(worsening pain|pain)\b", "SYMPTOM"),
    (r"\b(desaturation|hypoxia|hypoxemia)\b", "SYMPTOM"),
    (r"\b(acute kidney injury|aki)\b", "DIAGNOSIS"),
    (r"\b(acute respiratory failure)\b", "DIAGNOSIS"),
    (r"\b(community-acquired pneumonia|pneumonia)\b", "DIAGNOSIS"),
    (r"\b(ischemic stroke|stroke|infarct)\b", "DIAGNOSIS"),
    (r"\b(atrial fibrillation|afib|a-fib)\b", "DIAGNOSIS"),
    (r"\b(hypertension)\b", "DIAGNOSIS"),
    (r"\b(diabetes mellitus|type 2 diabetes|diabetes)\b", "DIAGNOSIS"),
    (r"\b(hyperlipidemia)\b", "DIAGNOSIS"),
    (r"\b(total knee arthroplasty|tka)\b", "PROCEDURE"),
    (r"\b(mri brain|ct head|chest x-ray|cxr|ekg)\b", "PROCEDURE"),
    (r"\b(tpa|ceftriaxone|azithromycin|metoprolol|amlodipine|oxycodone|insulin|oxygen)\b", "MEDICATION"),
    (r"\b(bp\s*\d+/\d+)\b", "VITAL"),
    (r"\b(hr\s*\d+)\b", "VITAL"),
    (r"\b(temp\s*\d+(\.\d+)?)\b", "VITAL"),
    (r"\b(creatinine\s*(bumped to|up to)?\s*\d+(\.\d+)?)\b", "LAB"),
]

NORMALIZATION_RULES: List[Tuple[str, str]] = [
    (r"\bexpressive aphasia\b|\baphasia\b", "aphasia"),
    (r"\bleft-sided weakness\b|\bright-sided weakness\b|\bweakness\b", "weakness"),
    (r"\bproductive cough\b|\bcough\b", "cough"),
    (r"\bafib\b|\ba-fib\b|\batrial fibrillation\b", "atrial fibrillation"),
    (r"\baki\b|\bacute kidney injury\b", "acute kidney injury"),
    (r"\bsob\b|\bshortness of breath\b", "shortness of breath"),
    (r"\bcommunity-acquired pneumonia\b|\bpneumonia\b", "pneumonia"),
    (r"\bischemic stroke\b|\bstroke\b|\binfarct\b", "ischemic stroke"),
    (r"\btka\b|\btotal knee arthroplasty\b", "total knee arthroplasty"),
    (r"\bhypoxia\b|\bhypoxemia\b|\bdesaturation\b|\bacute respiratory failure\b", "respiratory compromise"),
    (r"\bblurry vision\b|\bvision changes\b", "blurry vision"),
]

DOMAIN_KEYWORDS = {
    "neurologic": ["weakness", "aphasia", "facial droop", "stroke", "vision"],
    "respiratory": ["shortness of breath", "cough", "pneumonia", "oxygen", "desaturation", "hypoxia", "respiratory"],
    "cardiovascular": ["atrial fibrillation", "afib", "hypertension", "palpitations", "bp", "hr"],
    "renal": ["acute kidney injury", "aki", "creatinine"],
    "musculoskeletal": ["knee", "arthroplasty", "pain"],
    "infectious": ["fever", "pneumonia", "sputum", "antibiotic"],
    "metabolic": ["diabetes", "insulin", "blood sugar"],
}


def _build_blank_pipeline():
    nlp = spacy.blank("en")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    return nlp


try:
    nlp = spacy.load("en_core_sci_sm")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    EXTRACTOR_BACKEND = "scispacy"
    EXTRACTOR_WARNINGS: List[str] = []
except OSError:
    nlp = _build_blank_pipeline()
    EXTRACTOR_BACKEND = "rules"
    EXTRACTOR_WARNINGS = [
        "en_core_sci_sm not installed; using deterministic clinical phrase matcher fallback.",
    ]


def normalize_entity_text(text: str) -> str:
    lowered = text.lower().strip()
    for pattern, replacement in NORMALIZATION_RULES:
        if re.search(pattern, lowered):
            return replacement
    lowered = re.sub(r"[^a-z0-9\s/-]", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def infer_domain(text: str) -> str:
    lowered = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return domain
    return "general"


def _heuristic_label(text: str) -> str:
    lowered = text.lower()
    for pattern, label in CLINICAL_PATTERNS:
        if re.search(pattern, lowered):
            return label
    return "CLINICAL_ENTITY"


def _rule_based_entities(text: str) -> List[Dict[str, object]]:
    entities: List[Dict[str, object]] = []
    for pattern, label in CLINICAL_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            entities.append(
                {
                    "text": match.group(0),
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                }
            )
    return entities


def extract_entities(text: str) -> List[Dict[str, object]]:
    """
    Extracts clinical entities with scispaCy when available and supplements
    the result with deterministic clinical phrase matching so the pipeline
    remains testable without external model providers.
    """
    doc = nlp(text)
    entities: List[Dict[str, object]] = []

    if EXTRACTOR_BACKEND == "scispacy":
        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "label": _heuristic_label(ent.text),
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )

    entities.extend(_rule_based_entities(text))

    deduped: Dict[Tuple[int, int, str, str], Dict[str, object]] = {}
    for entity in entities:
        key = (
            int(entity["start"]),
            int(entity["end"]),
            str(entity["text"]).lower(),
            str(entity["label"]),
        )
        deduped[key] = entity

    return sorted(deduped.values(), key=lambda item: (int(item["start"]), int(item["end"])))


def extract_sentences(text: str) -> List[Dict[str, object]]:
    doc = nlp(text)
    sentences: List[Dict[str, object]] = []
    for sent in doc.sents:
        cleaned = sent.text.strip()
        if not cleaned:
            continue
        sentences.append(
            {
                "text": cleaned,
                "start": sent.start_char,
                "end": sent.end_char,
            }
        )
    return sentences
