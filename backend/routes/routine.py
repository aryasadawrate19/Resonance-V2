"""
POST /api/routine — AI skincare routine generation endpoint.
"""

from fastapi import APIRouter
from schemas.models import RoutineRequest
from engines.routine_generator import get_routine_generator

router = APIRouter()


@router.post("/routine")
async def generate_routine(request: RoutineRequest):
    """
    Generate a personalized skincare routine using Gemini API.
    Falls back to static routines if API unavailable.
    """
    generator = get_routine_generator()

    skin_profile = {
        "skin_type": request.skin_type,
        "acne_severity": request.acne_severity,
        "acne_coverage_pct": request.acne_coverage_pct,
        "lesion_count": request.lesion_count,
        "hyperpigmentation_pct": request.hyperpigmentation_pct,
        "skin_health_score": request.skin_health_score,
        "sleep_quality": request.sleep_quality,
        "diet_quality": request.diet_quality,
        "stress_level": request.stress_level,
        "climate_zone": request.climate_zone,
    }

    result = await generator.generate_routine(skin_profile)
    return result
