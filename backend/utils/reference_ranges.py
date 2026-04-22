"""
Reference ranges and helper functions for common blood test markers.
"""

from __future__ import annotations

from typing import Any

REFERENCE_RANGES = {
    "hemoglobin": {
        "male": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
        "female": {"min": 12.0, "max": 15.5, "unit": "g/dL"},
    },
    "wbc": {"min": 4.5, "max": 11.0, "unit": "10^3/uL"},
    "rbc": {
        "male": {"min": 4.5, "max": 5.9, "unit": "10^6/uL"},
        "female": {"min": 4.0, "max": 5.2, "unit": "10^6/uL"},
    },
    "platelets": {"min": 150, "max": 400, "unit": "10^3/uL"},
    "hematocrit": {
        "male": {"min": 41, "max": 53, "unit": "%"},
        "female": {"min": 36, "max": 46, "unit": "%"},
    },
    "mcv": {"min": 80, "max": 100, "unit": "fL"},
    "mch": {"min": 27, "max": 33, "unit": "pg"},
    "mchc": {"min": 32, "max": 36, "unit": "g/dL"},
    "neutrophils": {"min": 40, "max": 70, "unit": "%"},
    "lymphocytes": {"min": 20, "max": 40, "unit": "%"},
    "monocytes": {"min": 2, "max": 8, "unit": "%"},
    "eosinophils": {"min": 1, "max": 4, "unit": "%"},
    "basophils": {"min": 0, "max": 1, "unit": "%"},
    "glucose_fasting": {"min": 70, "max": 100, "unit": "mg/dL"},
    "glucose_random": {"min": 70, "max": 140, "unit": "mg/dL"},
    "hba1c": {"min": 4.0, "max": 5.6, "unit": "%"},
    "total_cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    "ldl": {"min": 0, "max": 100, "unit": "mg/dL"},
    "hdl": {
        "male": {"min": 40, "max": 999, "unit": "mg/dL"},
        "female": {"min": 50, "max": 999, "unit": "mg/dL"},
    },
    "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
    "creatinine": {
        "male": {"min": 0.7, "max": 1.3, "unit": "mg/dL"},
        "female": {"min": 0.6, "max": 1.1, "unit": "mg/dL"},
    },
    "urea": {"min": 7, "max": 20, "unit": "mg/dL"},
    "uric_acid": {
        "male": {"min": 3.5, "max": 7.2, "unit": "mg/dL"},
        "female": {"min": 2.6, "max": 6.0, "unit": "mg/dL"},
    },
    "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
    "potassium": {"min": 3.5, "max": 5.1, "unit": "mEq/L"},
    "calcium": {"min": 8.5, "max": 10.5, "unit": "mg/dL"},
    "tsh": {"min": 0.4, "max": 4.0, "unit": "mIU/L"},
    "t3": {"min": 80, "max": 200, "unit": "ng/dL"},
    "t4": {"min": 5.0, "max": 12.0, "unit": "ug/dL"},
    "bilirubin_total": {"min": 0.2, "max": 1.2, "unit": "mg/dL"},
    "sgot_ast": {"min": 10, "max": 40, "unit": "U/L"},
    "sgpt_alt": {"min": 7, "max": 56, "unit": "U/L"},
    "alkaline_phosphatase": {"min": 44, "max": 147, "unit": "U/L"},
    "albumin": {"min": 3.4, "max": 5.4, "unit": "g/dL"},
    "vitamin_d": {"min": 20, "max": 50, "unit": "ng/mL"},
    "vitamin_b12": {"min": 200, "max": 900, "unit": "pg/mL"},
    "iron": {
        "male": {"min": 65, "max": 175, "unit": "ug/dL"},
        "female": {"min": 50, "max": 170, "unit": "ug/dL"},
    },
    "ferritin": {
        "male": {"min": 20, "max": 250, "unit": "ng/mL"},
        "female": {"min": 10, "max": 120, "unit": "ng/mL"},
    },
}


def classify_value(marker_name: str, value: float, gender: str = "unknown") -> dict[str, Any]:
    """
    Classify a marker value against its standard reference range.

    Returns:
        {
            "status": "normal" | "low" | "high" | "unknown",
            "range": "min-max unit",
            "unit": "unit"
        }
    """
    marker_key = marker_name.lower().strip()
    range_definition = REFERENCE_RANGES.get(marker_key)
    if not range_definition:
        return {"status": "unknown", "range": "N/A", "unit": ""}

    resolved_range = _resolve_range(range_definition, gender)
    minimum = resolved_range["min"]
    maximum = resolved_range["max"]
    unit = resolved_range["unit"]

    if value < minimum:
        status = "low"
    elif value > maximum:
        status = "high"
    else:
        status = "normal"

    display_max = _format_number(maximum) if maximum < 999 else "999+"
    range_text = f"{_format_number(minimum)}-{display_max} {unit}"
    return {"status": status, "range": range_text, "unit": unit}


def get_reference_range_details(marker_name: str, gender: str = "unknown") -> dict[str, Any] | None:
    """Return normalized min/max/unit details for a marker and gender."""
    marker_key = marker_name.lower().strip()
    range_definition = REFERENCE_RANGES.get(marker_key)
    if not range_definition:
        return None
    return _resolve_range(range_definition, gender)


def _resolve_range(range_definition: dict[str, Any], gender: str) -> dict[str, Any]:
    if "male" in range_definition or "female" in range_definition:
        if gender == "female" and "female" in range_definition:
            return range_definition["female"]
        if gender == "male" and "male" in range_definition:
            return range_definition["male"]
        if "male" in range_definition:
            return range_definition["male"]
        return range_definition["female"]
    return range_definition


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")
