"""
Recommendation generation using Gemini.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from google.genai import types

from utils.gemini_client import (
    call_with_retries,
    get_gemini_client,
    get_gemini_model_candidates,
    get_gemini_model_name,
)

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "This tool provides general health information only. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider."
)

SYSTEM_PROMPT = f"""
You are a health advisor providing general wellness recommendations based on blood test results.
You are NOT diagnosing any disease.
Always recommend consulting a doctor for medical decisions.
Be specific, practical, and evidence-based.
Return ONLY valid JSON.

Return exactly:
{{
  "summary": "Overall health summary in 2-3 sentences",
  "key_points": ["Short calm bullet points"],
  "urgent_flags": ["Any values needing immediate medical attention"],
  "recommendations": [
    {{
      "category": "Diet|Exercise|Lifestyle|Follow-up",
      "priority": "high|medium|low",
      "title": "Short title",
      "detail": "Specific actionable advice"
    }}
  ],
  "disclaimer": "{MEDICAL_DISCLAIMER}"
}}
""".strip()


def generate_recommendations(analysis: dict, patient_info: dict) -> dict[str, Any]:
    """Generate non-diagnostic wellness recommendations from abnormal results."""
    client = get_gemini_client()
    prompt = _build_user_prompt(analysis, patient_info)
    failures: list[str] = []

    for model_name in get_gemini_model_candidates():
        try:
            response = call_with_retries(
                lambda model_name=model_name: client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
            )
            break
        except Exception as exc:
            logger.warning("Gemini recommendation failed with model '%s': %s", model_name, exc)
            failures.append(f"{model_name}: {exc}")
    else:
        preferred_model = get_gemini_model_name()
        failure_summary = " | ".join(failures)
        raise RuntimeError(
            f"AI recommendation failed after retries. Preferred model '{preferred_model}'. Attempts: {failure_summary}"
        )

    try:
        parsed = json.loads(_strip_code_fences((response.text or "").strip()))
    except json.JSONDecodeError:
        logger.error("Malformed recommendation JSON: %s", response.text if response else "")
        return _fallback_response()

    return _normalize_recommendations(parsed)


def _build_user_prompt(analysis: dict, patient_info: dict) -> str:
    patient_age = patient_info.get("age") or "unknown"
    patient_gender = patient_info.get("gender") or "unknown"
    interpretation = analysis.get("interpretation", {})

    structured_markers: list[str] = []
    for group_name in ("high", "low", "normal"):
        for entry in analysis.get(group_name, []):
            severity = entry["severity"] if entry.get("severity") else "normal"
            structured_markers.append(
                f"- {entry['marker']}: value={entry['value']} unit={entry['unit']} "
                f"range_min={entry.get('range_min')} range_max={entry.get('range_max')} "
                f"status={group_name} severity={severity} deviation={round(entry.get('deviation', 0.0), 3)} "
                f"borderline={entry.get('borderline', False)}"
            )

    marker_text = "\n".join(structured_markers) if structured_markers else "- No markers found."

    return (
        f"Patient age: {patient_age}\n"
        f"Patient gender: {patient_gender}\n"
        f"Overall status: {interpretation.get('overall_status', 'unknown')}\n"
        f"Health score: {interpretation.get('health_score', 'unknown')}\n"
        f"Rule-based insights: {interpretation.get('rule_based_insights', [])}\n"
        "Structured markers:\n"
        f"{marker_text}\n\n"
        "Generate a concise clinical-style summary, calm key points, and practical recommendations. Do not diagnose disease."
    )


def _normalize_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    recommendations = []
    for item in payload.get("recommendations", []):
        category = str(item.get("category", "Lifestyle")).strip()
        if category not in {"Diet", "Exercise", "Lifestyle", "Follow-up"}:
            category = "Lifestyle"

        priority = str(item.get("priority", "low")).strip().lower()
        if priority not in {"high", "medium", "low"}:
            priority = "low"

        title = str(item.get("title", "General wellness advice")).strip() or "General wellness advice"
        detail = str(item.get("detail", "")).strip() or "Discuss these results with a healthcare professional."
        recommendations.append(
            {
                "category": category,
                "priority": priority,
                "title": title,
                "detail": detail,
            }
        )

    if not recommendations:
        recommendations = _fallback_response()["recommendations"]

    urgent_flags = [str(flag).strip() for flag in payload.get("urgent_flags", []) if str(flag).strip()]
    key_points = [str(item).strip() for item in payload.get("key_points", []) if str(item).strip()]

    return {
        "summary": str(payload.get("summary", "Blood test analysis completed.")).strip()
        or "Blood test analysis completed.",
        "key_points": key_points,
        "urgent_flags": urgent_flags,
        "recommendations": recommendations,
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def _strip_code_fences(text: str) -> str:
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def _fallback_response() -> dict[str, Any]:
    return {
        "summary": "The report was analyzed, but the recommendation response was partially unavailable.",
        "key_points": ["Review the structured findings and discuss them with a qualified healthcare provider if symptoms are present."],
        "urgent_flags": [],
        "recommendations": [
            {
                "category": "Follow-up",
                "priority": "high",
                "title": "Review with your doctor",
                "detail": "Please review these results with a qualified healthcare provider before making medical decisions.",
            }
        ],
        "disclaimer": MEDICAL_DISCLAIMER,
    }
