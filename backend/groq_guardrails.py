import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class GroqSettings:
    api_key: str
    model: str
    max_retries: int
    min_interval_seconds: float
    backoff_seconds: float
    timeout_seconds: float


_last_request_time = 0.0
_request_lock = threading.Lock()


def load_groq_settings() -> GroqSettings:
    return GroqSettings(
        api_key=os.getenv("GROQ_API_KEY", "").strip(),
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip(),
        max_retries=max(0, int(os.getenv("GROQ_MAX_RETRIES", "1"))),
        min_interval_seconds=max(0.0, float(os.getenv("GROQ_MIN_INTERVAL_SECONDS", "4"))),
        backoff_seconds=max(0.0, float(os.getenv("GROQ_BACKOFF_SECONDS", "8"))),
        timeout_seconds=max(1.0, float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))),
    )


def wait_for_groq_slot(settings: GroqSettings | None = None) -> None:
    global _last_request_time

    settings = settings or load_groq_settings()
    with _request_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        remaining = settings.min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        _last_request_time = time.monotonic()


def call_with_groq_limits(operation: Callable[[], T], settings: GroqSettings | None = None) -> T:
    settings = settings or load_groq_settings()
    last_error: Exception | None = None

    for attempt in range(settings.max_retries + 1):
        wait_for_groq_slot(settings)
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= settings.max_retries:
                raise
            time.sleep(settings.backoff_seconds * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError("Groq operation failed without raising a concrete exception.")
