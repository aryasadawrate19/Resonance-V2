"""
Predictive Engine — 7-day and 30-day skin projection.
Uses evidence-based decay rates modified by lifestyle inputs.
"""


def predict(
    skin_health_score: int,
    acne_severity: str,
    lesion_count: int,
    lifestyle: dict,
) -> dict:
    """
    Generate 7-day and 30-day skin health projections.

    Formula: projected = baseline × (1 + base_rate × weeks) × lifestyle_modifier

    Args:
        skin_health_score: current composite score (0-100)
        acne_severity: current severity string
        lesion_count: current lesion count
        lifestyle: dict with sleep_quality, diet_quality, stress_level (1-5 each)

    Returns:
        dict with prediction_7d and prediction_30d.
    """
    baseline = skin_health_score

    # Base rate: +8% worsening per week without intervention (inverted since higher = healthier)
    base_rate_per_week = -0.08  # Score decreases without intervention

    # ─── Lifestyle modifier (-0.3 to +0.3) ───
    sleep = lifestyle.get("sleep_quality", 3)
    diet = lifestyle.get("diet_quality", 3)
    stress = lifestyle.get("stress_level", 3)

    # Each factor contributes to modifier:
    # Good habits (4-5) → positive (score improves)
    # Bad habits (1-2) → negative (score worsens faster)
    sleep_mod = (sleep - 3) * 0.05    # -0.1 to +0.1
    diet_mod = (diet - 3) * 0.05      # -0.1 to +0.1
    stress_mod = (3 - stress) * 0.05  # Inverted: high stress = bad

    lifestyle_modifier = sleep_mod + diet_mod + stress_mod
    lifestyle_modifier = max(-0.3, min(0.3, lifestyle_modifier))

    # ─── 7-day projection (1 week) ───
    total_rate_7d = base_rate_per_week + lifestyle_modifier
    projected_7d = int(baseline * (1 + total_rate_7d))
    projected_7d = max(0, min(100, projected_7d))
    delta_7d = projected_7d - baseline

    # ─── 30-day projection (~4.3 weeks) ───
    weeks_30d = 30 / 7
    total_rate_30d = (base_rate_per_week * weeks_30d) + (lifestyle_modifier * weeks_30d * 0.7)
    projected_30d = int(baseline * (1 + total_rate_30d))
    projected_30d = max(0, min(100, projected_30d))
    delta_30d = projected_30d - baseline

    # Generate descriptive labels
    label_7d = _generate_label(delta_7d, "7 days")
    label_30d = _generate_label(delta_30d, "30 days")

    return {
        "prediction_7d": {
            "projected_score": projected_7d,
            "delta": delta_7d,
            "label": label_7d,
        },
        "prediction_30d": {
            "projected_score": projected_30d,
            "delta": delta_30d,
            "label": label_30d,
        },
        "lifestyle_modifier": round(lifestyle_modifier, 3),
    }


def _generate_label(delta: int, timeframe: str) -> str:
    """Generate a human-readable projection label."""
    if delta > 5:
        return f"Likely to improve by {abs(delta)}% in {timeframe}"
    elif delta > 0:
        return f"Slight improvement expected in {timeframe}"
    elif delta == 0:
        return f"Expected to remain stable over {timeframe}"
    elif delta > -5:
        return f"Slight worsening possible in {timeframe}"
    elif delta > -15:
        return f"Likely to worsen by {abs(delta)}% in {timeframe}"
    else:
        return f"Significant worsening projected ({abs(delta)}%) in {timeframe} without intervention"
