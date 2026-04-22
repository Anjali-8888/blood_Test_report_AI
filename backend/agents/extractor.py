"""
Blood value extraction using Gemini from already-extracted PDF text.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from google.genai import types

from utils.gemini_client import (
    call_with_retries,
    get_gemini_client,
    get_gemini_model_candidates,
    get_gemini_model_name,
)
from utils.reference_ranges import REFERENCE_RANGES

logger = logging.getLogger(__name__)

STANDARD_KEYS = list(REFERENCE_RANGES.keys())

SYSTEM_PROMPT = f"""
You are a medical data extraction specialist.
Extract all blood test values from the provided lab report text.

Return ONLY valid JSON with no markdown and no explanation.
Map report test names to these standard keys where possible:
{", ".join(STANDARD_KEYS)}

Rules:
- Extract patient_name, patient_age, patient_gender, and report_date if present.
- patient_gender must be "male", "female", or "unknown".
- Return numeric values only inside the values object.
- If units clearly imply conversion to the standard range unit, convert them.
- Omit values you cannot extract confidently.
- Preserve the original raw marker names in raw_markers_found.

Return exactly this shape:
{{
  "patient_name": null,
  "patient_age": null,
  "patient_gender": "unknown",
  "report_date": null,
  "values": {{
    "hemoglobin": 14.2
  }},
  "raw_markers_found": ["Hemoglobin"]
}}
""".strip()


def extract_blood_values(
    pdf_text: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
) -> dict[str, Any]:
    """Use Gemini to extract normalized blood markers from lab-report text or PDF bytes."""
    if not pdf_text and not pdf_bytes:
        raise ValueError("No readable PDF text or PDF bytes were provided for extraction.")

    client = get_gemini_client()
    contents = _build_contents(pdf_text=pdf_text, pdf_bytes=pdf_bytes)
    failures: list[str] = []

    for model_name in get_gemini_model_candidates():
        try:
            response = call_with_retries(
                lambda model_name=model_name: client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
            )
            break
        except Exception as exc:
            logger.warning("Gemini extraction failed with model '%s': %s", model_name, exc)
            failures.append(f"{model_name}: {exc}")
    else:
        preferred_model = get_gemini_model_name()
        failure_summary = " | ".join(failures)
        raise RuntimeError(
            f"AI extraction failed after retries. Preferred model '{preferred_model}'. Attempts: {failure_summary}"
        )

    payload = _parse_json_response(response.text if response and response.text else "")
    extracted = _normalize_extraction_payload(payload)
    if not extracted["values"]:
        raise ValueError("No recognizable blood test values found.")
    return extracted


def _parse_json_response(raw_text: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(raw_text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Malformed extraction JSON: %s", cleaned[:600])
        raise RuntimeError("AI extraction returned malformed JSON.") from exc


def _normalize_extraction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_values: dict[str, float] = {}
    raw_values = payload.get("values") or {}

    for key, value in raw_values.items():
        normalized_key = str(key).strip().lower()
        if normalized_key not in REFERENCE_RANGES:
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        normalized_values[normalized_key] = _normalize_marker_value(normalized_key, numeric_value)

    raw_markers = payload.get("raw_markers_found") or list(raw_values.keys())
    return {
        "patient_name": payload.get("patient_name"),
        "patient_age": _string_or_none(payload.get("patient_age")),
        "patient_gender": _normalize_gender(payload.get("patient_gender")),
        "report_date": _string_or_none(payload.get("report_date")),
        "values": normalized_values,
        "raw_markers_found": [str(item) for item in raw_markers if str(item).strip()],
    }


def _normalize_gender(gender: Any) -> str:
    value = str(gender or "").strip().lower()
    if value in {"male", "female"}:
        return value
    return "unknown"


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _strip_code_fences(text: str) -> str:
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def _build_contents(pdf_text: Optional[str], pdf_bytes: Optional[bytes]):
    instruction = (
        "Extract all blood test values from this lab report. "
        "Use the attached PDF as the source of truth. "
        "If native extracted text is provided, use it only as an additional hint."
    )

    parts = [types.Part.from_text(text=instruction)]

    if pdf_text and pdf_text.strip():
        parts.append(
            types.Part.from_text(
                text=f"NATIVE EXTRACTED TEXT HINT:\n{pdf_text[:12000]}"
            )
        )

    if pdf_bytes:
        parts.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))

    return parts


def _normalize_marker_value(marker_key: str, value: float) -> float:
    """
    Normalize common lab-report magnitudes into the same units used by REFERENCE_RANGES.

    Many CBC reports print absolute counts like:
    - WBC: 9000 cells/cumm -> should be 9.0 in 10^3/uL ranges
    - Platelets: 150000 /cumm -> should be 150 in 10^3/uL ranges
    """
    if marker_key in {"wbc", "platelets"} and value >= 1000:
        return value / 1000.0

    if marker_key == "rbc" and value >= 100:
        return value / 1_000_000.0

    return value
