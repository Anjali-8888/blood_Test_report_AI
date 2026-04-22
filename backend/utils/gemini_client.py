"""
Shared Gemini helpers built on the current Google Gen AI SDK.
"""

from __future__ import annotations

import os
import time
from typing import Callable, TypeVar

from google import genai

T = TypeVar("T")


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def get_gemini_model_name() -> str:
    configured = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    if configured.startswith("models/"):
        return configured.split("/", 1)[1]
    return configured or "gemini-2.5-flash"


def get_gemini_model_candidates() -> list[str]:
    primary = get_gemini_model_name()
    candidates = [
        primary,
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def should_retry_gemini_error(exc: Exception) -> bool:
    message = str(exc).upper()
    retry_markers = [
        "503",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "RATE LIMIT",
        "INTERNAL",
        "TIMEOUT",
        "DEADLINE",
    ]
    return any(marker in message for marker in retry_markers)


def call_with_retries(func: Callable[[], T], attempts: int = 3, base_delay: float = 1.2) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt >= attempts or not should_retry_gemini_error(exc):
                raise
            time.sleep(base_delay * attempt)
    raise last_error if last_error else RuntimeError("Unknown Gemini retry failure.")
