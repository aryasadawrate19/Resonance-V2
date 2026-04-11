"""
Pydantic request/response models for DermaTwin API.
Matches PRD Section 08 response schema.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Request Models ───

class LifestyleInput(BaseModel):
    skin_type: str = Field(default="combination", description="oily / dry / combination / normal")
    sleep_quality: int = Field(default=3, ge=1, le=5, description="1-5 scale")
    diet_quality: int = Field(default=3, ge=1, le=5, description="1-5 scale")
    stress_level: int = Field(default=3, ge=1, le=5, description="1-5 scale")
    climate_zone: str = Field(default="tropical", description="tropical / arid / temperate / cold / humid")
    age: Optional[int] = Field(default=None, ge=10, le=100)
    gender: Optional[str] = Field(default=None, description="male / female / other")


class SimulationRequest(BaseModel):
    skin_health_score: int = Field(..., ge=0, le=100)
    acne_severity: str
    acne_coverage_pct: float
    lesion_count: int
    hyperpigmentation_pct: float
    lifestyle: LifestyleInput
    interventions: list[str] = Field(default_factory=list)


class RoutineRequest(BaseModel):
    skin_type: str
    acne_severity: str
    acne_coverage_pct: float
    lesion_count: int
    hyperpigmentation_pct: float
    skin_health_score: int
    sleep_quality: int
    diet_quality: int
    stress_level: int
    climate_zone: str


class HistorySaveRequest(BaseModel):
    uid: str
    scan_data: dict


# ─── Response Models ───

class LesionInfo(BaseModel):
    id: str
    lesion_class: str = Field(description="comedonal / inflammatory / other")
    bbox: list[int] = Field(description="[x1, y1, x2, y2]")
    confidence: float


class ZoneInfo(BaseModel):
    forehead: float = Field(default=0.0, ge=0, le=1)
    left_cheek: float = Field(default=0.0, ge=0, le=1)
    right_cheek: float = Field(default=0.0, ge=0, le=1)
    nose: float = Field(default=0.0, ge=0, le=1)
    chin_jawline: float = Field(default=0.0, ge=0, le=1)


class ScoreBreakdown(BaseModel):
    acne: int = Field(ge=0, le=100)
    lesion: int = Field(ge=0, le=100)
    pigmentation: int = Field(ge=0, le=100)
    zone: int = Field(ge=0, le=100)


class PredictionResult(BaseModel):
    projected_score: int
    delta: int
    label: str


class AnalyzeResponse(BaseModel):
    annotated_image: str = Field(description="Base64-encoded annotated PNG")
    acne_severity: str
    acne_coverage_pct: float
    lesions: list[LesionInfo]
    lesion_count: int
    zones: ZoneInfo
    hyperpigmentation_pct: float
    skin_health_score: int
    score_breakdown: ScoreBreakdown
    prediction_7d: PredictionResult
    prediction_30d: PredictionResult
    severity_confidence: float = Field(default=0.0)
    severity_source: str = Field(default="hybrid_fusion")


class SimulationResult(BaseModel):
    original_score: int
    projected_score: int
    total_acne_delta: float
    total_pigmentation_delta: float
    intervention_details: list[dict]
    projected_severity: str


class RoutineStep(BaseModel):
    step: int
    action: str
    product_type: str
    key_ingredient: str
    why: str
    budget_option: Optional[str] = None
    premium_option: Optional[str] = None


class RoutineResponse(BaseModel):
    morning_routine: list[RoutineStep]
    night_routine: list[RoutineStep]
    priority_ingredients: list[str]
    expected_timeline: str
    climate_note: str
    disclaimer: str


class HistoryEntry(BaseModel):
    scan_id: str
    timestamp: str
    skin_health_score: int
    acne_severity: str
    lesion_count: int
    hyperpigmentation_pct: float
