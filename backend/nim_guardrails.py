import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class NimSettings:
    api_key: str
    model: str
    base_url: str
    max_retries: int
    min_interval_seconds: float
    backoff_seconds: float
    timeout_seconds: float


_last_request_time = 0.0
_request_lock = threading.Lock()


def load_nim_settings() -> NimSettings:
    return NimSettings(
        api_key=os.getenv("NVIDIA_NIM_API_KEY", "").strip(),
        model=os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct").strip(),
        base_url=os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").strip(),
        max_retries=max(0, int(os.getenv("NVIDIA_NIM_MAX_RETRIES", "1"))),
        min_interval_seconds=max(0.0, float(os.getenv("NVIDIA_NIM_MIN_INTERVAL_SECONDS", "1.0"))),
        backoff_seconds=max(0.0, float(os.getenv("NVIDIA_NIM_BACKOFF_SECONDS", "4.0"))),
        timeout_seconds=max(1.0, float(os.getenv("NVIDIA_NIM_TIMEOUT_SECONDS", "30.0"))),
    )


def wait_for_nim_slot(settings: NimSettings | None = None) -> None:
    global _last_request_time

    settings = settings or load_nim_settings()
    with _request_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        remaining = settings.min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        _last_request_time = time.monotonic()


def call_with_nim_limits(operation: Callable[[], T], settings: NimSettings | None = None) -> T:
    settings = settings or load_nim_settings()
    last_error: Exception | None = None

    for attempt in range(settings.max_retries + 1):
        wait_for_nim_slot(settings)
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= settings.max_retries:
                raise
            time.sleep(settings.backoff_seconds * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError("NVIDIA NIM operation failed without raising a concrete exception.")
