"""
Severity Grader — Wraps HybridSkinAnalyzer for acne severity classification.
Uses HF Transformers as primary, rule-based as fallback.
"""

import numpy as np
from PIL import Image
import logging

from cv_modules.hybrid_model import get_hybrid_analyzer

logger = logging.getLogger(__name__)


def grade_severity(
    pil_image: Image.Image,
    lesions: list,
) -> dict:
    """
    Grade acne severity using hybrid model.

    Args:
        pil_image: PIL Image of the face (full image, not cropped)
        lesions: list of detected lesion dicts from lesion_detector

    Returns:
        dict with:
            - severity: str ("Clear"/"Mild"/"Moderate"/"Severe")
            - confidence: float (0-1)
            - acne_coverage_pct: float
            - lesion_count: int
            - lesion_types: dict
            - source: str
    """
    analyzer = get_hybrid_analyzer()

    # Step 1: HF model global severity classification
    model_result = analyzer.classify_global_severity(pil_image)

    # Step 2: Count lesions by type
    lesion_types = {"inflammatory": 0, "comedonal": 0, "other": 0}
    for lesion in lesions:
        hint = lesion.get("type_hint", "other")
        if hint in lesion_types:
            lesion_types[hint] += 1
        else:
            lesion_types["other"] += 1

    lesion_count = len(lesions)

    # Step 3: Fuse model prediction with lesion data
    fused = analyzer.fuse_results(model_result, lesion_count, lesion_types)

    logger.info(
        f"Severity: {fused['severity']} (confidence={fused['confidence']}, "
        f"source={fused['source']}, lesions={lesion_count})"
    )

    return fused
