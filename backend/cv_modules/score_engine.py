"""
Skin Health Score Engine — Weighted composite score calculation.
"""


def compute_score(
    acne_severity: str,
    lesion_count: int,
    hyperpigmentation_pct: float,
    zone_inflammation: dict,
) -> dict:
    """
    Compute the weighted Skin Health Score (0-100, higher = healthier).

    Formula:
        score = 0.35 × acne_sub + 0.25 × lesion_sub + 0.20 × pigmentation_sub + 0.20 × zone_sub

    Returns:
        dict with:
            - skin_health_score: int (0-100)
            - breakdown: {acne: int, lesion: int, pigmentation: int, zone: int}
    """
    # ─── Acne severity sub-score (inverted: healthier = higher) ───
    severity_scores = {
        "Clear": 95,
        "Mild": 70,
        "Moderate": 45,
        "Severe": 15,
    }
    acne_sub = severity_scores.get(acne_severity, 50)

    # ─── Lesion density sub-score ───
    if lesion_count == 0:
        lesion_sub = 100
    elif lesion_count <= 2:
        lesion_sub = 85
    elif lesion_count <= 5:
        lesion_sub = 70
    elif lesion_count <= 10:
        lesion_sub = 50
    elif lesion_count <= 15:
        lesion_sub = 30
    else:
        lesion_sub = max(10, 30 - (lesion_count - 15) * 2)

    # ─── Pigmentation sub-score ───
    if hyperpigmentation_pct < 5:
        pigmentation_sub = 95
    elif hyperpigmentation_pct < 10:
        pigmentation_sub = 75
    elif hyperpigmentation_pct < 20:
        pigmentation_sub = 55
    elif hyperpigmentation_pct < 30:
        pigmentation_sub = 35
    else:
        pigmentation_sub = 15

    # ─── Zone inflammation sub-score ───
    # Average inflammation across zones (each 0-1, higher = more inflamed)
    zone_values = [
        zone_inflammation.get("forehead", 0),
        zone_inflammation.get("left_cheek", 0),
        zone_inflammation.get("right_cheek", 0),
        zone_inflammation.get("nose", 0),
        zone_inflammation.get("chin_jawline", 0),
    ]
    avg_inflammation = sum(zone_values) / max(len(zone_values), 1)
    zone_sub = int(max(0, 100 - (avg_inflammation * 100)))

    # ─── Weighted composite ───
    score = int(
        0.35 * acne_sub
        + 0.25 * lesion_sub
        + 0.20 * pigmentation_sub
        + 0.20 * zone_sub
    )

    # Clamp to 0-100
    score = max(0, min(100, score))

    return {
        "skin_health_score": score,
        "breakdown": {
            "acne": acne_sub,
            "lesion": lesion_sub,
            "pigmentation": pigmentation_sub,
            "zone": zone_sub,
        },
    }
