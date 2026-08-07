import logging
import os
from copy import deepcopy
from functools import lru_cache
from typing import Any, Tuple

logger = logging.getLogger("translation_layer")

RIVA_MODEL_DEFAULT = "nvidia/riva-translate-4b-instruct-v2"

SUPPORTED = {
    "de": ("Helsinki-NLP/opus-mt-de-en", "Helsinki-NLP/opus-mt-en-de"),
    "fr": ("Helsinki-NLP/opus-mt-fr-en", "Helsinki-NLP/opus-mt-en-fr"),
    "nl": ("Helsinki-NLP/opus-mt-nl-en", "Helsinki-NLP/opus-mt-en-nl"),
    "es": ("Helsinki-NLP/opus-mt-es-en", "Helsinki-NLP/opus-mt-en-es"),
}

RIVA_SUPPORTED_LANGUAGES = {
    "en", "de", "fr", "nl", "es", "zh", "ja", "ko", "it", "pt", "ru",
    "hi", "ar", "tr", "cs", "da", "el", "hu", "fi", "no", "pl", "ro",
    "sk", "sv", "bg", "uk", "hr", "et", "sl", "lt", "lv", "id", "th", "vi",
}

SUPPORTED_WITH_ENGLISH = {"en", *SUPPORTED.keys(), *RIVA_SUPPORTED_LANGUAGES}

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


def get_active_translation_provider() -> dict:
    nim_key = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
    riva_model = os.getenv("NVIDIA_RIVA_MODEL", RIVA_MODEL_DEFAULT).strip()
    backend = os.getenv("TRANSLATION_BACKEND", "auto").lower().strip()

    if backend == "riva" or (backend == "auto" and nim_key):
        active = "riva"
    elif TRANSFORMERS_AVAILABLE:
        active = "marian"
    else:
        active = "none"

    return {
        "active_provider": active,
        "riva_model": riva_model,
        "riva_configured": bool(nim_key),
        "marian_available": TRANSFORMERS_AVAILABLE,
    }


def get_supported_languages() -> list[str]:
    provider = get_active_translation_provider()
    if provider["active_provider"] == "riva":
        return sorted(list(RIVA_SUPPORTED_LANGUAGES))
    return ["en", *SUPPORTED.keys()]


def detect_input_language(text: str, requested_lang: str = "auto") -> Tuple[str, list[str]]:
    normalized = (requested_lang or "auto").strip().lower()
    warnings: list[str] = []

    if normalized != "auto":
        if normalized not in SUPPORTED_WITH_ENGLISH:
            raise TranslationLayerError(
                f"Unsupported language '{requested_lang}'. Supported values: auto, en, de, fr, nl, es, zh, ja, etc."
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


def _translate_riva(text: str, src_lang: str, target_lang: str = "en") -> str:
    """
    Translate text using NVIDIA's nvidia/riva-translate-4b-instruct-v2 model via NIM API.
    """
    import requests
    from backend.nim_guardrails import call_with_nim_limits, load_nim_settings

    nim_settings = load_nim_settings()
    if not nim_settings.api_key:
        raise TranslationLayerError("NVIDIA_NIM_API_KEY is not configured for Riva translation.")

    model_name = os.getenv("NVIDIA_RIVA_MODEL", RIVA_MODEL_DEFAULT).strip()
    lang_pair = f"{src_lang.lower()}-{target_lang.lower()}"

    # nvidia/riva-translate-4b-instruct-v2 expects exact language pair tag (e.g. "en-de", "de-en") as system content
    system_prompt = lang_pair

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    def _do_post() -> str:
        url = f"{nim_settings.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
        }
        headers = {
            "Authorization": f"Bearer {nim_settings.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=nim_settings.timeout_seconds)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```") and content.endswith("```"):
                lines = content.splitlines()
                if len(lines) >= 3:
                    content = "\n".join(lines[1:-1]).strip()
            return content
        raise RuntimeError(f"Riva translation HTTP {resp.status_code}: {resp.text[:200]}")

    return call_with_nim_limits(_do_post, nim_settings)


def translate(
    text: str,
    src_lang: str,
    to_english: bool = True,
    target_lang: str = "en",
    backend: str = "auto",
) -> str:
    if not text:
        return text

    tgt = "en" if to_english else (target_lang if target_lang != "en" else src_lang)
    if src_lang == tgt:
        return text

    configured_backend = os.getenv("TRANSLATION_BACKEND", backend).lower().strip()
    nim_api_key = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

    # Try Riva Translate if configured or auto with NIM API key present
    if configured_backend == "riva" or (configured_backend == "auto" and nim_api_key):
        try:
            return _translate_riva(text, src_lang=src_lang, target_lang=tgt)
        except Exception as exc:
            riva_model = os.getenv("NVIDIA_RIVA_MODEL", RIVA_MODEL_DEFAULT).strip()
            logger.warning(
                "Riva translation (%s) failed: %s. Falling back to MarianMT.",
                riva_model,
                exc,
            )

    # MarianMT Fallback logic
    if src_lang not in SUPPORTED and tgt not in SUPPORTED:
        raise TranslationLayerError(f"Unsupported language pair '{src_lang}' -> '{tgt}'.")

    model_key = src_lang if to_english else tgt
    if model_key not in SUPPORTED:
        raise TranslationLayerError(f"Unsupported language '{model_key}'.")

    model_name = SUPPORTED[model_key][0 if to_english else 1]
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

