"""
FastAPI application entry point for the blood test analysis system.
"""

from __future__ import annotations

import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.analyzer import analyze_blood_values
from agents.extractor import extract_blood_values
from agents.recommender import MEDICAL_DISCLAIMER, generate_recommendations
from models.schemas import (
    AnalysisSummary,
    AnalyzeResponse,
    BloodMarker,
    ErrorResponse,
    InterpretationResult,
    PatientInfo,
    RecommendationResult,
)
from utils.gemini_client import get_gemini_model_name
from utils.ocr import extract_text_with_huggingface_ocr
from utils.pdf_parser import extract_text_from_pdf
from utils.reference_ranges import REFERENCE_RANGES

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
logger.info("Configured GEMINI_MODEL=%s", get_gemini_model_name())
logger.info("Configured HF OCR=%s", "enabled" if os.getenv("HF_TOKEN") else "disabled")

app = FastAPI(
    title="Blood Test Analysis API",
    version="1.0",
    description=(
        "Upload a blood test PDF, extract markers from text-based reports, "
        "classify them against reference ranges, and receive general wellness guidance."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "1.0"}


@app.get("/reference-ranges")
async def reference_ranges() -> dict:
    return REFERENCE_RANGES


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_report(
    file: UploadFile = File(...),
    gender: str = Form(default="unknown"),
) -> AnalyzeResponse:
    start_time = time.perf_counter()

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")

    pdf_text = None
    try:
        pdf_text = extract_text_from_pdf(file_bytes)
    except ValueError:
        logger.info("Native PDF text extraction was weak or unavailable; using Gemini document understanding fallback.")

    if not pdf_text and os.getenv("HF_TOKEN"):
        try:
            pdf_text = extract_text_with_huggingface_ocr(file_bytes)
            logger.info("Recovered document text using Hugging Face OCR fallback.")
        except Exception as exc:
            logger.warning("Hugging Face OCR fallback failed: %s", exc)

    try:
        extracted = extract_blood_values(pdf_text=pdf_text, pdf_bytes=file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    normalized_gender = gender.lower().strip()
    if normalized_gender in {"male", "female"}:
        extracted["patient_gender"] = normalized_gender

    analysis = analyze_blood_values(extracted)

    try:
        recommendations = generate_recommendations(analysis, analysis["patient_info"])
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    markers = _build_marker_response(analysis)
    summary = AnalysisSummary(
        total_markers=len(markers),
        normal_count=len(analysis["normal"]),
        low_count=len(analysis["low"]),
        high_count=len(analysis["high"]),
        unknown_count=len(analysis["unknown"]),
        overall_status=analysis["interpretation"]["overall_status"],
        health_score=analysis["interpretation"]["health_score"],
    )

    patient_info = PatientInfo(**analysis["patient_info"])
    interpretation = InterpretationResult(**analysis["interpretation"])
    recommendation_result = RecommendationResult(**recommendations)

    return AnalyzeResponse(
        patient_info=patient_info,
        markers=markers,
        summary=summary,
        interpretation=interpretation,
        insights=analysis["interpretation"].get("rule_based_insights", []),
        recommendations=recommendation_result,
        processing_time_seconds=round(time.perf_counter() - start_time, 2),
    )


def _build_marker_response(analysis: dict) -> list[BloodMarker]:
    markers: list[BloodMarker] = []
    for status in ("high", "low", "normal", "unknown"):
        for entry in analysis.get(status, []):
            markers.append(
                BloodMarker(
                    name=entry["display_name"],
                    key=entry["marker"],
                    value=float(entry["value"]),
                    unit=entry.get("unit", ""),
                    status=status,
                    severity=entry.get("severity"),
                    normal_range=entry.get("range", "N/A"),
                    range={"min": entry.get("range_min"), "max": entry.get("range_max")},
                    deviation=round(float(entry.get("deviation", 0.0)), 3),
                    borderline=bool(entry.get("borderline", False)),
                )
            )
    return markers


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "detail": str(exc)})
