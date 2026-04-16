"""
Treatment Simulator — Project outcomes based on intervention toggles.
Uses evidence-based decay curves from published dermatology literature.
"""

# Intervention impact table from PRD
INTERVENTIONS = {
    "salicylic_acid": {
        "label": "Salicylic Acid (2%)",
        "acne_impact_2w": -0.35,   # -30 to -40%
        "pigmentation_4w": -0.02,  # Minimal
        "description": "BHA exfoliant that unclogs pores and reduces inflammation",
    },
    "improved_sleep": {
        "label": "Improved Sleep (+2 hrs)",
        "acne_impact_2w": -0.15,
        "pigmentation_4w": -0.05,
        "description": "Better sleep reduces cortisol-driven inflammation",
    },
    "reduced_sugar": {
        "label": "Reduced Sugar Intake",
        "acne_impact_2w": -0.20,
        "pigmentation_4w": -0.02,
        "description": "Lower glycemic index reduces insulin-driven sebum production",
    },
    "niacinamide": {
        "label": "Niacinamide Serum",
        "acne_impact_2w": -0.10,
        "pigmentation_4w": -0.25,
        "description": "Vitamin B3 derivative that reduces pigmentation and strengthens skin barrier",
    },
    "spf_daily": {
        "label": "SPF 50 Daily",
        "acne_impact_2w": -0.02,
        "pigmentation_4w": -0.20,
        "description": "Sunscreen prevents UV-induced pigmentation and post-inflammatory marks",
    },
    "hydration": {
        "label": "Hydration (+2L Water)",
        "acne_impact_2w": -0.10,
        "pigmentation_4w": -0.05,
        "description": "Improved hydration supports skin barrier function and healing",
    },
}


def simulate(
    skin_health_score: int,
    acne_severity: str,
    acne_coverage_pct: float,
    hyperpigmentation_pct: float,
    interventions: list[str],
    lifestyle: dict = None,
) -> dict:
    """
    Simulate treatment outcomes based on selected interventions.

    Args:
        skin_health_score: current score (0-100)
        acne_severity: current severity string
        acne_coverage_pct: current acne coverage %
        hyperpigmentation_pct: current pigmentation %
        interventions: list of intervention keys to toggle
        lifestyle: optional lifestyle data

    Returns:
        dict with projected outcomes per intervention
    """
    total_acne_delta = 0.0
    total_pigment_delta = 0.0
    acne_multiplier = 1.0
    pigment_multiplier = 1.0
    details = []

    for intervention_key in interventions:
        intervention = INTERVENTIONS.get(intervention_key)
        if intervention is None:
            continue

        acne_delta = intervention["acne_impact_2w"]
        pigment_delta = intervention["pigmentation_4w"]

        total_acne_delta += acne_delta * acne_multiplier
        total_pigment_delta += pigment_delta * pigment_multiplier
        acne_multiplier *= 0.7
        pigment_multiplier *= 0.7

        details.append({
            "key": intervention_key,
            "label": intervention["label"],
            "description": intervention["description"],
            "acne_impact_pct": round(acne_delta * 100, 1),
            "pigmentation_impact_pct": round(pigment_delta * 100, 1),
        })

    # Cap combined effects (diminishing returns)
    total_acne_delta = max(-0.70, total_acne_delta)
    total_pigment_delta = max(-0.50, total_pigment_delta)

    # Project new acne coverage
    projected_acne_coverage = acne_coverage_pct * (1 + total_acne_delta)
    projected_acne_coverage = max(0, projected_acne_coverage)

    # Project new pigmentation
    projected_pigmentation = hyperpigmentation_pct * (1 + total_pigment_delta)
    projected_pigmentation = max(0, projected_pigmentation)

    # Estimate new score
    # Rough improvement: acne is 35% of score, pigmentation is 20%
    acne_score_boost = abs(total_acne_delta) * 35
    pigment_score_boost = abs(total_pigment_delta) * 20
    projected_score = min(100, int(skin_health_score + acne_score_boost + pigment_score_boost))

    # Project new severity
    projected_severity = _project_severity(acne_severity, total_acne_delta)

    return {
        "original_score": skin_health_score,
        "projected_score": projected_score,
        "total_acne_delta": round(total_acne_delta * 100, 1),
        "total_pigmentation_delta": round(total_pigment_delta * 100, 1),
        "projected_acne_coverage": round(projected_acne_coverage, 1),
        "projected_pigmentation": round(projected_pigmentation, 1),
        "projected_severity": projected_severity,
        "intervention_details": details,
        "disclaimer": "These projections are evidence-based estimates, not medical diagnoses. Individual results may vary.",
    }


def _project_severity(current: str, acne_delta: float) -> str:
    """Project severity change based on acne improvement."""
    severity_order = ["Clear", "Mild", "Moderate", "Severe"]
    current_idx = severity_order.index(current) if current in severity_order else 2

    # Significant improvement → reduce severity
    if acne_delta <= -0.40:
        new_idx = max(0, current_idx - 2)
    elif acne_delta <= -0.20:
        new_idx = max(0, current_idx - 1)
    else:
        new_idx = current_idx

    return severity_order[new_idx]


def get_available_interventions() -> list:
    """Return all available interventions for the frontend."""
    return [
        {
            "key": key,
            "label": val["label"],
            "description": val["description"],
            "acne_impact": f"{val['acne_impact_2w'] * 100:+.0f}%",
            "pigmentation_impact": f"{val['pigmentation_4w'] * 100:+.0f}%",
        }
        for key, val in INTERVENTIONS.items()
    ]
