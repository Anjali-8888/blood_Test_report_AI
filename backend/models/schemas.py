"""
Pydantic response schemas for the API.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    gender: str = "unknown"
    report_date: Optional[str] = None


class BloodMarker(BaseModel):
    name: str
    key: str
    value: float
    unit: str
    status: Literal["normal", "low", "high", "unknown"]
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    normal_range: str
    range: dict
    deviation: float = 0.0
    borderline: bool = False


class AnalysisSummary(BaseModel):
    total_markers: int
    normal_count: int
    low_count: int
    high_count: int
    unknown_count: int = 0
    overall_status: Optional[str] = None
    health_score: Optional[int] = None


class InterpretationResult(BaseModel):
    health_score: int
    overall_status: str
    clinical_summary: str
    rule_based_insights: List[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    category: Literal["Diet", "Exercise", "Lifestyle", "Follow-up"]
    priority: Literal["high", "medium", "low"]
    title: str = Field(..., max_length=120)
    detail: str


class RecommendationResult(BaseModel):
    summary: str
    key_points: List[str] = Field(default_factory=list)
    urgent_flags: List[str] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    disclaimer: str


class AnalyzeResponse(BaseModel):
    patient_info: PatientInfo
    markers: List[BloodMarker]
    summary: AnalysisSummary
    interpretation: InterpretationResult
    insights: List[str] = Field(default_factory=list)
    recommendations: RecommendationResult
    processing_time_seconds: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
