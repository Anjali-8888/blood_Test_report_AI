"""
Pure-Python classification logic for extracted blood markers.
"""

from __future__ import annotations

from utils.reference_ranges import classify_value, get_reference_range_details

DISPLAY_NAMES = {
    "hemoglobin": "Hemoglobin",
    "wbc": "WBC",
    "rbc": "RBC",
    "platelets": "Platelets",
    "hematocrit": "Hematocrit",
    "mcv": "MCV",
    "mch": "MCH",
    "mchc": "MCHC",
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "monocytes": "Monocytes",
    "eosinophils": "Eosinophils",
    "basophils": "Basophils",
    "glucose_fasting": "Glucose Fasting",
    "glucose_random": "Glucose Random",
    "hba1c": "HbA1c",
    "total_cholesterol": "Total Cholesterol",
    "ldl": "LDL",
    "hdl": "HDL",
    "triglycerides": "Triglycerides",
    "creatinine": "Creatinine",
    "urea": "Urea",
    "uric_acid": "Uric Acid",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "calcium": "Calcium",
    "tsh": "TSH",
    "t3": "T3",
    "t4": "T4",
    "bilirubin_total": "Bilirubin Total",
    "sgot_ast": "SGOT / AST",
    "sgpt_alt": "SGPT / ALT",
    "alkaline_phosphatase": "Alkaline Phosphatase",
    "albumin": "Albumin",
    "vitamin_d": "Vitamin D",
    "vitamin_b12": "Vitamin B12",
    "iron": "Iron",
    "ferritin": "Ferritin",
}

SEVERITY_ORDER = {"severe": 3, "moderate": 2, "mild": 1, None: 0}


def analyze_blood_values(extracted_data: dict) -> dict:
    """Classify each extracted marker as normal, low, high, or unknown."""
    gender = str(extracted_data.get("patient_gender", "unknown")).lower()
    values = extracted_data.get("values", {})

    result = {
        "normal": [],
        "low": [],
        "high": [],
        "unknown": [],
        "patient_info": {
            "name": extracted_data.get("patient_name"),
            "age": extracted_data.get("patient_age"),
            "gender": gender,
            "report_date": extracted_data.get("report_date"),
        },
    }

    for marker, value in values.items():
        classification = classify_value(marker, value, gender)
        entry = {
            "marker": marker,
            "display_name": DISPLAY_NAMES.get(marker, marker.replace("_", " ").title()),
            "value": value,
            "unit": classification["unit"],
            "range": classification["range"],
            "range_min": None,
            "range_max": None,
            "severity": None,
            "deviation": 0.0,
            "borderline": False,
        }

        if classification["status"] == "unknown":
            result["unknown"].append(entry)
            continue

        if classification["status"] in {"low", "high"}:
            range_details = get_reference_range_details(marker, gender)
            entry["range_min"] = range_details["min"]
            entry["range_max"] = range_details["max"]
            entry["severity"] = _calculate_severity(
                value=value,
                status=classification["status"],
                minimum=range_details["min"],
                maximum=range_details["max"],
            )
            entry["deviation"] = _calculate_deviation(
                value=value,
                status=classification["status"],
                minimum=range_details["min"],
                maximum=range_details["max"],
            )
            result[classification["status"]].append(entry)
        else:
            range_details = get_reference_range_details(marker, gender)
            if range_details:
                entry["range_min"] = range_details["min"]
                entry["range_max"] = range_details["max"]
                entry["borderline"] = value == range_details["min"] or value == range_details["max"]
            result["normal"].append(entry)

    result["high"].sort(key=_severity_sort_key, reverse=True)
    result["low"].sort(key=_severity_sort_key, reverse=True)
    result["interpretation"] = _build_interpretation(result)
    return result


def _calculate_severity(value: float, status: str, minimum: float, maximum: float) -> str:
    deviation = _calculate_deviation(value, status, minimum, maximum)
    if deviation < 0.10:
        return "mild"
    if deviation < 0.25:
        return "moderate"
    return "severe"


def _calculate_deviation(value: float, status: str, minimum: float, maximum: float) -> float:
    if status == "low":
        return ((minimum - value) / minimum) if minimum else 0.0
    return ((value - maximum) / maximum) if maximum else 0.0


def _severity_sort_key(item: dict) -> tuple[int, float]:
    return (SEVERITY_ORDER.get(item.get("severity"), 0), float(item.get("value", 0)))


def _build_interpretation(analysis: dict) -> dict:
    abnormal_entries = analysis.get("high", []) + analysis.get("low", [])
    statuses = {}
    for status in ("high", "low", "normal", "unknown"):
        for entry in analysis.get(status, []):
            statuses[entry["marker"]] = status

    score = _calculate_health_score(abnormal_entries)
    overall_status = _label_health_score(score)
    insights = _build_marker_insights(abnormal_entries, statuses)
    insights.extend(_build_correlation_insights(statuses))

    return {
        "health_score": score,
        "overall_status": overall_status,
        "clinical_summary": _build_clinical_summary(analysis, overall_status, insights),
        "rule_based_insights": insights[:8],
    }


def _calculate_health_score(abnormal_entries: list[dict]) -> int:
    penalties = {"mild": 5, "moderate": 10, "severe": 20}
    score = 100
    for entry in abnormal_entries:
        score -= penalties.get(entry.get("severity"), 5)
    return max(0, min(100, score))


def _label_health_score(score: int) -> str:
    if score >= 90:
        return "all_good"
    if score >= 75:
        return "minor_issues"
    if score >= 55:
        return "needs_attention"
    return "consult_doctor"


def _build_marker_insights(abnormal_entries: list[dict], statuses: dict[str, str]) -> list[str]:
    templates = {
        ("hemoglobin", "low"): "Hemoglobin is mildly below range and may fit an early anemia pattern worth monitoring.",
        ("hematocrit", "high"): "Hematocrit is elevated, which can appear with dehydration or hemoconcentration and may merit a repeat test if symptoms fit.",
        ("platelets", "low"): "Platelets are near or below the lower limit, so repeat monitoring is reasonable if bruising or bleeding symptoms are present.",
        ("ldl", "high"): "LDL is above goal, suggesting a lipid-management opportunity through diet, exercise, and clinician follow-up.",
        ("vitamin_d", "low"): "Vitamin D is below range, which is common and usually addressed with sunlight, diet, and clinician-guided supplementation.",
        ("hba1c", "high"): "HbA1c is elevated and can reflect longer-term glucose imbalance that deserves follow-up.",
        ("glucose_fasting", "high"): "Fasting glucose is above range, so repeat testing and glucose-focused follow-up would be sensible.",
        ("creatinine", "high"): "Creatinine is elevated and should be reviewed with kidney function context and hydration status.",
    }

    insights: list[str] = []
    for entry in abnormal_entries:
        key = (entry["marker"], statuses.get(entry["marker"], "low"))
        template = templates.get(key)
        if template:
            insights.append(template)
            continue
        direction = "above" if key[1] == "high" else "below"
        insights.append(
            f"{entry['display_name']} is {direction} the usual range ({entry['range']}), so it should be interpreted in the context of symptoms and follow-up trends."
        )
    return insights


def _build_correlation_insights(statuses: dict[str, str]) -> list[str]:
    insights: list[str] = []

    if statuses.get("hemoglobin") == "low" and statuses.get("hematocrit") == "high":
        insights.append(
            "Low hemoglobin alongside high hematocrit can be an inconsistent pattern, so hydration status, sample quality, or repeat testing may be worth considering."
        )

    if statuses.get("hemoglobin") == "low" and (
        statuses.get("mcv") == "low" or statuses.get("mch") == "low" or statuses.get("ferritin") == "low" or statuses.get("iron") == "low"
    ):
        insights.append(
            "The low hemoglobin pattern with low red-cell indices or iron markers can fit an iron-deficiency style picture and supports clinician follow-up."
        )

    if statuses.get("glucose_fasting") == "high" and statuses.get("hba1c") == "high":
        insights.append(
            "High fasting glucose together with elevated HbA1c suggests a more persistent glucose-control issue rather than a one-off reading."
        )

    if statuses.get("ldl") == "high" and (
        statuses.get("triglycerides") == "high" or statuses.get("hdl") == "low"
    ):
        insights.append(
            "The lipid pattern suggests a broader cardiometabolic risk signal, so lifestyle tightening and clinician review would be reasonable."
        )

    if statuses.get("creatinine") == "high" and statuses.get("urea") == "high":
        insights.append(
            "Creatinine and urea both being elevated can point to kidney-function or hydration-related follow-up needs."
        )

    return insights


def _build_clinical_summary(analysis: dict, overall_status: str, insights: list[str]) -> str:
    abnormal_count = len(analysis.get("high", [])) + len(analysis.get("low", []))
    severe_count = len(
        [entry for entry in analysis.get("high", []) + analysis.get("low", []) if entry.get("severity") == "severe"]
    )

    if abnormal_count == 0:
        return "Overall: markers are within expected ranges, with no obvious rule-based concerns in this report."

    if severe_count > 0:
        return (
            f"Overall: {overall_status.replace('_', ' ')} with at least one clearly abnormal marker. "
            f"The strongest signals are summarized here: {insights[0] if insights else 'professional follow-up is advisable.'}"
        )

    return (
        f"Overall: {overall_status.replace('_', ' ')} with {abnormal_count} abnormal marker"
        f"{'' if abnormal_count == 1 else 's'}. "
        f"{insights[0] if insights else 'These results look non-critical but worth monitoring over time.'}"
    )
