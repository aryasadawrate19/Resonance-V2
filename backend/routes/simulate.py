"""
POST /api/simulate — Treatment simulation endpoint.
"""

from fastapi import APIRouter
from schemas.models import SimulationRequest
from engines.simulator import simulate, get_available_interventions

router = APIRouter()


@router.post("/simulate")
async def simulate_treatment(request: SimulationRequest):
    """
    Simulate treatment outcomes based on selected interventions.
    Returns projected scores and deltas.
    """
    result = simulate(
        skin_health_score=request.skin_health_score,
        acne_severity=request.acne_severity,
        acne_coverage_pct=request.acne_coverage_pct,
        hyperpigmentation_pct=request.hyperpigmentation_pct,
        interventions=request.interventions,
        lifestyle=request.lifestyle.model_dump() if request.lifestyle else {},
    )
    return result


@router.get("/interventions")
async def list_interventions():
    """Return all available interventions for the frontend."""
    return {"interventions": get_available_interventions()}
