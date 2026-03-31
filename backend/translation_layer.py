from copy import deepcopy
from functools import lru_cache
from typing import Any, Tuple

SUPPORTED = {
    "de": ("Helsinki-NLP/opus-mt-de-en", "Helsinki-NLP/opus-mt-en-de"),
    "fr": ("Helsinki-NLP/opus-mt-fr-en", "Helsinki-NLP/opus-mt-en-fr"),
    "nl": ("Helsinki-NLP/opus-mt-nl-en", "Helsinki-NLP/opus-mt-en-nl"),
    "es": ("Helsinki-NLP/opus-mt-es-en", "Helsinki-NLP/opus-mt-en-es"),
}
SUPPORTED_WITH_ENGLISH = {"en", *SUPPORTED.keys()}
TRANSLATABLE_FIELDS = {
    "raw_text",
    "text",
    "text_span",
    "sentence_text",
    "description",
    "rationale",
    "summary",
    "warnings",
    "details",
}


class TranslationLayerError(RuntimeError):
    pass


try:
    from langdetect import DetectorFactory, LangDetectException, detect

    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LangDetectException = Exception
    detect = None
    LANGDETECT_AVAILABLE = False

try:
    from transformers import MarianMTModel, MarianTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    MarianMTModel = None
    MarianTokenizer = None
    TRANSFORMERS_AVAILABLE = False


@lru_cache(maxsize=8)
def _load_model(model_name: str):
    if not TRANSFORMERS_AVAILABLE:
        raise TranslationLayerError(
            "Translation dependencies are not installed. Install transformers, sentencepiece, and torch."
        )
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model


def _split_text(text: str, limit: int = 450) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n"):
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph
    if current:
        chunks.append(current)
    return chunks or [text]


def detect_input_language(text: str, requested_lang: str = "auto") -> Tuple[str, list[str]]:
    normalized = (requested_lang or "auto").strip().lower()
    warnings: list[str] = []

    if normalized != "auto":
        if normalized not in SUPPORTED_WITH_ENGLISH:
            raise TranslationLayerError(
                f"Unsupported language '{requested_lang}'. Supported values: auto, en, de, fr, nl, es."
            )
        return normalized, warnings

    if not text.strip():
        return "en", warnings

    if not LANGDETECT_AVAILABLE:
        warnings.append("langdetect not installed; defaulting input language to English.")
        return "en", warnings

    try:
        detected = detect(text)
    except LangDetectException:
        warnings.append("Unable to detect input language; defaulting to English.")
        return "en", warnings

    if detected not in SUPPORTED_WITH_ENGLISH:
        warnings.append(
            f"Detected unsupported language '{detected}'; pipeline will continue in English without translation."
        )
        return "en", warnings

    return detected, warnings


def translate(text: str, src_lang: str, to_english: bool = True) -> str:
    if not text or src_lang == "en":
        return text
    if src_lang not in SUPPORTED:
        raise TranslationLayerError(f"Unsupported language '{src_lang}'.")

    model_name = SUPPORTED[src_lang][0 if to_english else 1]
    tokenizer, model = _load_model(model_name)
    translated_chunks: list[str] = []

    for chunk in _split_text(text):
        tokens = tokenizer(
            [chunk],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        translated = model.generate(**tokens)
        translated_chunks.append(tokenizer.decode(translated[0], skip_special_tokens=True))

    return "\n".join(translated_chunks)


def _translate_payload(value: Any, language: str, parent_key: str | None = None) -> Any:
    if language == "en":
        return value

    if isinstance(value, dict):
        translated: dict[str, Any] = {}
        for key, item in value.items():
            translated[key] = _translate_payload(item, language, key)
        return translated

    if isinstance(value, list):
        if parent_key in {"warnings", "details"}:
            return [translate(item, language, to_english=False) if isinstance(item, str) else item for item in value]
        return [_translate_payload(item, language, parent_key) for item in value]

    if isinstance(value, str) and parent_key in TRANSLATABLE_FIELDS:
        return translate(value, language, to_english=False)

    return value


def build_display_report(report_payload: dict, language: str) -> dict:
    translated_payload = deepcopy(report_payload)
    return _translate_payload(translated_payload, language)
