"""
POST /api/analyze — Main analysis endpoint.
Runs the full hybrid CV pipeline on an uploaded face image.
"""

import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from cv_modules.preprocessor import preprocess_image, validate_image
from cv_modules.face_mesh import get_face_mesh_analyzer
from cv_modules.lesion_detector import get_lesion_detector
from cv_modules.severity_grader import grade_severity
from cv_modules.pigmentation import analyze_pigmentation
from cv_modules.score_engine import compute_score
from cv_modules.overlay_renderer import render_overlays
from engines.predictor import predict

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_skin(
    image: UploadFile = File(...),
    lifestyle: Optional[str] = Form(default=None),
):
    """
    Upload a face image + optional lifestyle data.
    Returns full analysis with annotated overlay image.
    """
    try:
        # ─── Parse lifestyle input ───
        lifestyle_data = {}
        if lifestyle:
            try:
                lifestyle_data = json.loads(lifestyle)
            except json.JSONDecodeError:
                lifestyle_data = {}

        # ─── Step 1: Image preprocessing ───
        image_bytes = await image.read()

        is_valid, msg = validate_image(image_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        preprocessed = preprocess_image(image_bytes)
        original_pil = preprocessed["original_pil"]
        original_np = preprocessed["original_np"]
        processed_np = preprocessed["processed_np"]

        logger.info(f"Image preprocessed: {preprocessed['original_width']}×{preprocessed['original_height']}")

        # ─── Step 2: Face mesh detection ───
        face_analyzer = get_face_mesh_analyzer()
        face_result = face_analyzer.analyze(original_np)

        face_detected = face_result["face_detected"]
        if not face_detected:
            logger.warning("No face clearly detected, proceeding with best effort")

        face_mask = face_result.get("face_mask")
        zones = face_result.get("zones", {})
        landmarks = face_result.get("landmarks")

        logger.info(f"Face detected: {face_detected}, zones: {list(zones.keys())}")

        # ─── Step 3: Lesion detection ───
        detector = get_lesion_detector()
        lesions = detector.detect(original_np, face_mask)
        logger.info(f"Detected {len(lesions)} lesions")

        # ─── Step 4-6: Severity grading (HF model + fusion) ───
        severity_result = grade_severity(original_pil, lesions)
        acne_severity = severity_result["severity"]
        acne_coverage = severity_result["acne_coverage_pct"]
        severity_confidence = severity_result["confidence"]
        severity_source = severity_result["source"]

        logger.info(f"Severity: {acne_severity} ({severity_source}, conf={severity_confidence})")

        # ─── Step 7: Pigmentation analysis ───
        pigment_result = analyze_pigmentation(original_np, face_mask)
        hyperpigmentation_pct = pigment_result["coverage_pct"]

        logger.info(f"Pigmentation: {hyperpigmentation_pct}% ({pigment_result['coverage_category']})")

        # ─── Step 8: Zone inflammation scoring ───
        zone_inflammation = _compute_zone_inflammation(lesions, zones)

        # ─── Step 9: Score computation ───
        score_result = compute_score(
            acne_severity=acne_severity,
            lesion_count=len(lesions),
            hyperpigmentation_pct=hyperpigmentation_pct,
            zone_inflammation=zone_inflammation,
        )
        skin_health_score = score_result["skin_health_score"]
        score_breakdown = score_result["breakdown"]

        logger.info(f"Skin Health Score: {skin_health_score}/100")

        # ─── Step 10: Prediction ───
        predictions = predict(
            skin_health_score=skin_health_score,
            acne_severity=acne_severity,
            lesion_count=len(lesions),
            lifestyle=lifestyle_data,
        )

        # ─── Step 11: Overlay rendering ───
        annotated_image = render_overlays(
            original_pil=original_pil,
            lesions=lesions,
            zones=zones,
            pigmentation_contours=pigment_result["contours"],
            pigmentation_coverage=hyperpigmentation_pct,
            severity=acne_severity,
            landmarks=landmarks,
            skin_health_score=skin_health_score,
        )

        logger.info("Analysis complete — overlay rendered")

        # ─── Assemble response ───
        response = {
            "annotated_image": annotated_image,
            "acne_severity": acne_severity,
            "acne_coverage_pct": round(acne_coverage, 1),
            "lesions": [
                {
                    "id": l["id"],
                    "lesion_class": l.get("type_hint", "other"),
                    "bbox": l["bbox"],
                    "confidence": l["confidence"],
                }
                for l in lesions
            ],
            "lesion_count": len(lesions),
            "zones": zone_inflammation,
            "face_detected": face_detected,
            "zones_approximate": not face_detected,
            "hyperpigmentation_pct": round(hyperpigmentation_pct, 1),
            "skin_health_score": skin_health_score,
            "score_breakdown": score_breakdown,
            "prediction_7d": predictions["prediction_7d"],
            "prediction_30d": predictions["prediction_30d"],
            "severity_confidence": severity_confidence,
            "severity_source": severity_source,
            "ita_angle": pigment_result.get("ita_angle", 0),
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


def _compute_zone_inflammation(lesions: list, zones: dict) -> dict:
    """Compute per-zone inflammation scores based on lesion overlap."""
    zone_scores = {
        "forehead": 0.0,
        "left_cheek": 0.0,
        "right_cheek": 0.0,
        "nose": 0.0,
        "chin_jawline": 0.0,
    }

    if not zones or not lesions:
        return zone_scores

    # Count lesions per zone (by bbox center)
    zone_lesion_counts = {z: 0 for z in zone_scores}

    for lesion in lesions:
        x1, y1, x2, y2 = lesion["bbox"]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        for zone_name, points in zones.items():
            if zone_name not in zone_scores:
                continue
            if not points:
                continue

            if _point_in_polygon(cx, cy, points):
                zone_lesion_counts[zone_name] += 1
                break

    # Convert counts to 0-1 inflammation scores
    for zone_name, count in zone_lesion_counts.items():
        if count == 0:
            zone_scores[zone_name] = 0.0
        elif count <= 2:
            zone_scores[zone_name] = 0.3
        elif count <= 5:
            zone_scores[zone_name] = 0.6
        else:
            zone_scores[zone_name] = min(1.0, 0.6 + count * 0.05)

    return zone_scores


def _point_in_polygon(x: int, y: int, polygon: list) -> bool:
    """Ray casting algorithm to check if point is inside polygon."""
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 0.0001) + xi):
            inside = not inside
        j = i

    return inside
