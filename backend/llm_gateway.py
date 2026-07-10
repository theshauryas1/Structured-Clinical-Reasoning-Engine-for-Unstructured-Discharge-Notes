"""
LLM Gateway — Centralized, security-hardened LLM router

Priority chain: NVIDIA NIM → Groq → Google Gemini (google-genai SDK v2)

Skills applied:
  - security-auditor: STRIDE, OWASP Top-10, prompt injection, PII redaction,
                      output safety, secrets-in-response guard
  - api-patterns: single gateway, clear error propagation, triple-provider fallback
  - gemini-api-dev: google-genai SDK v2, gemini-3-flash-preview, openai-compatible
                    messages→contents conversion
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests

from backend.groq_guardrails import call_with_groq_limits, load_groq_settings
from backend.nim_guardrails import call_with_nim_limits, load_nim_settings

logger = logging.getLogger("llm_gateway")

# ─── Tuneable limits ──────────────────────────────────────────────────────────
MAX_USER_INPUT_CHARS = 12_000
MAX_CONTEXT_MESSAGES = 30
MAX_OUTPUT_CHARS     = 8_000

# ─── Prompt injection patterns (security-auditor: STRIDE Tampering/Spoofing) ──
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)\bignore\b.{0,30}\binstruction", re.DOTALL),
    re.compile(r"(?i)\bforget\b.{0,30}\binstruction", re.DOTALL),
    re.compile(r"(?i)\bsystem\b.{0,30}\bprompt", re.DOTALL),
    re.compile(r"(?i)\bnew\b.{0,20}\bprompt", re.DOTALL),
    re.compile(r"(?i)\bdisregard\b.{0,30}\binstruction", re.DOTALL),
    re.compile(r"(?i)\byou\b.{0,10}\bmust\b.{0,10}\bnow\b", re.DOTALL),
    re.compile(r"(?i)\bact\b.{0,10}\bas\b.{0,10}\b(a|an)\b", re.DOTALL),
    re.compile(r"(?i)\boverride\b.{0,30}\binstruction", re.DOTALL),
    re.compile(r"(?i)\bpretend\b.{0,20}\byou\b.{0,20}\bare", re.DOTALL),
    re.compile(r"(?i)\bdeveloper\s+mode\b", re.DOTALL),
    re.compile(r"(?i)\bjailbreak\b", re.DOTALL),
    re.compile(r"(?i)\bdan\s+mode\b", re.DOTALL),
    re.compile(r"(?i)do\s+anything\s+now", re.DOTALL),
]

def _check_prompt_injection(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_PATTERNS)


# ─── PII Redaction (GDPR / HIPAA) ────────────────────────────────────────────
_PII_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL":       re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "PHONE":       re.compile(
        r"\+?\b\d{1,4}[.\-\s]?\(?\d{2,3}\)?[.\-\s]?\d{3,4}[.\-\s]?\d{3,4}\b|\b\d{10}\b"
    ),
    "SSN":         re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "NHS_NUMBER":  re.compile(r"\b\d{3}\s\d{3}\s\d{4}\b"),
    "DOB":         re.compile(
        r"\b(0?[1-9]|[12]\d|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](19|20)\d{2}\b"
    ),
    "IP_ADDRESS":  re.compile(
        r"\b((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
}

def _redact_pii(text: str) -> str:
    for label, pat in _PII_PATTERNS.items():
        text = pat.sub(f"<{label}_REDACTED>", text)
    return text


# ─── Output safety (security-auditor: Information Disclosure prevention) ──────
_SENSITIVE_KEYWORDS = [
    "GROQ_API_KEY", "NVIDIA_NIM_API_KEY", "GEMINI_API_KEY",
    "CLINICAL_REASONING_API_KEY", "private_key", "bearer",
]

def _is_output_safe(text: str) -> bool:
    lower = text.lower()
    for kw in _SENSITIVE_KEYWORDS:
        if kw.lower() in lower:
            logger.warning("Output safety: blocked keyword '%s' in LLM response.", kw)
            return False
    for env_var in ("GROQ_API_KEY", "NVIDIA_NIM_API_KEY", "GEMINI_API_KEY", "CLINICAL_REASONING_API_KEY"):
        val = os.environ.get(env_var, "")
        if val and val in text:
            logger.warning("Output safety: literal secret value found in LLM response — blocked.")
            return False
    return True


# ─── Message safety constants ─────────────────────────────────────────────────
_BLOCKED_MSG = (
    "[Security Alert: Your query contains patterns that violate our safety policy. "
    "Please focus your questions on the clinical context.]"
)
_UNSAFE_OUTPUT_MSG = (
    "[Security Alert: The generated response was blocked by output safety guardrails "
    "to prevent information leakage.]"
)


# ─── Sanitise message list ────────────────────────────────────────────────────
def _sanitise_messages(
    messages: List[Dict[str, str]],
    *,
    check_injection: bool = True,
) -> tuple[List[Dict[str, str]], Optional[str]]:
    trimmed = messages[-MAX_CONTEXT_MESSAGES:]
    cleaned: List[Dict[str, str]] = []
    for msg in trimmed:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            if len(content) > MAX_USER_INPUT_CHARS:
                content = content[:MAX_USER_INPUT_CHARS] + "\n[...truncated for safety]"
            if check_injection and _check_prompt_injection(content):
                logger.warning("LLM Gateway: prompt injection blocked.")
                return [], _BLOCKED_MSG
            content = _redact_pii(content)
        cleaned.append({"role": role, "content": content})
    return cleaned, None


# ─── Provider: NVIDIA NIM ─────────────────────────────────────────────────────
def _call_nim(msgs: List[Dict[str, str]], settings: Any) -> str:
    resp = requests.post(
        f"{settings.base_url.rstrip('/')}/chat/completions",
        json={"model": settings.model, "messages": msgs, "temperature": 0.2, "max_tokens": 1024},
        headers={"Authorization": f"Bearer {settings.api_key}", "Content-Type": "application/json"},
        timeout=settings.timeout_seconds,
    )
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    raise RuntimeError(f"NIM HTTP {resp.status_code}: {resp.text[:200]}")


# ─── Provider: Groq ───────────────────────────────────────────────────────────
def _call_groq(msgs: List[Dict[str, str]], settings: Any) -> str:
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={"model": settings.model, "messages": msgs, "temperature": 0.2, "max_tokens": 1024},
        headers={"Authorization": f"Bearer {settings.api_key}", "Content-Type": "application/json"},
        timeout=settings.timeout_seconds,
    )
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    raise RuntimeError(f"Groq HTTP {resp.status_code}: {resp.text[:200]}")


# ─── Provider: Google Gemini (REST API — v1beta generateContent) ──────────────
#
# Uses the same pattern as the user's curl command:
#   POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
#   Header: X-goog-api-key: <GEMINI_API_KEY>
#
# Pure requests — no SDK version pinning, works identically locally and in cloud
# (GCP Cloud Run, Render, Railway, Docker, etc.)
#
def _convert_to_gemini_contents(msgs: List[Dict[str, str]]) -> tuple:
    """
    Convert OpenAI-style messages → Gemini REST format.
      system    → system_instruction (merged, passed at top-level of request body)
      user      → role: "user"
      assistant → role: "model"  (Gemini naming convention)
    """
    system_parts: list[str] = []
    contents: list[dict] = []
    for msg in msgs:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "user":
            contents.append({"role": "user",  "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, contents


def _call_gemini(msgs: List[Dict[str, str]]) -> str:
    """
    Call Gemini via direct REST API (v1beta generateContent).

    Mirrors the curl command:
      curl https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent
           -H 'Content-Type: application/json'
           -H 'X-goog-api-key: <GEMINI_API_KEY>'
           -d '{"contents": [{"parts": [{"text": "..."}]}]}'
    """
    api_key  = os.environ.get("GEMINI_API_KEY", "").strip()
    model    = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    base_url = os.environ.get(
        "GEMINI_API_BASE",
        "https://generativelanguage.googleapis.com/v1beta",
    ).rstrip("/")

    if not api_key or api_key == "your_gemini_api_key_here":
        raise RuntimeError("GEMINI_API_KEY not configured.")

    system_instruction, contents = _convert_to_gemini_contents(msgs)

    # Build request body — same shape as the curl -d payload
    body: dict = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }
    if system_instruction:
        body["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    url = f"{base_url}/models/{model}:generateContent"

    resp = requests.post(
        url,
        json=body,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": api_key,   # matches the curl -H header exactly
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Gemini REST HTTP {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(
            f"Unexpected Gemini response shape: {exc}. Body: {str(data)[:200]}"
        )


# ─── Public gateway entry-point ───────────────────────────────────────────────

def call_llm_gateway(
    messages: List[Dict[str, str]],
    *,
    skip_injection_check: bool = False,
) -> str:
    """
    Security-hardened LLM router.

    Chain: NVIDIA NIM → Groq → Google Gemini
    Each provider is tried in order; first success wins.
    """
    # 1. Sanitise input
    cleaned, early_exit = _sanitise_messages(
        messages, check_injection=not skip_injection_check
    )
    if early_exit:
        return early_exit

    response_text = ""

    # 2. NVIDIA NIM (primary)
    nim_settings = load_nim_settings()
    if nim_settings.api_key:
        try:
            response_text = call_with_nim_limits(
                lambda: _call_nim(cleaned, nim_settings), nim_settings
            )
            logger.info("LLM Gateway: NIM success (%d chars)", len(response_text))
        except Exception as exc:
            logger.warning("LLM Gateway: NIM failed → trying Groq. Reason: %s", exc)

    # 3. Groq (first fallback)
    if not response_text:
        groq_settings = load_groq_settings()
        if groq_settings.api_key:
            try:
                response_text = call_with_groq_limits(
                    lambda: _call_groq(cleaned, groq_settings), groq_settings
                )
                logger.info("LLM Gateway: Groq success (%d chars)", len(response_text))
            except Exception as exc:
                logger.warning("LLM Gateway: Groq failed → trying Gemini. Reason: %s", exc)

    # 4. Google Gemini (second fallback)
    if not response_text:
        try:
            response_text = _call_gemini(cleaned)
            logger.info("LLM Gateway: Gemini success (%d chars)", len(response_text))
        except Exception as exc:
            logger.warning("LLM Gateway: Gemini failed. Reason: %s", exc)

    if not response_text:
        raise RuntimeError(
            "All LLM providers failed or no API keys configured (NIM, Groq, Gemini)."
        )

    # 5. Output safety check
    if not _is_output_safe(response_text):
        return _UNSAFE_OUTPUT_MSG

    # 6. Output length cap
    if len(response_text) > MAX_OUTPUT_CHARS:
        response_text = response_text[:MAX_OUTPUT_CHARS] + "\n\n[Response truncated]"

    return response_text
