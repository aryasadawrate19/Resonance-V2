"""
Hyperpigmentation Detection — OpenCV LAB color space analysis.
Step 7 (previously 4) of the CV pipeline.
"""

import numpy as np
import cv2
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def analyze_pigmentation(
    image_rgb: np.ndarray,
    face_mask: Optional[np.ndarray] = None,
) -> dict:
    """
    Detect hyperpigmentation using LAB color space analysis.

    Returns:
        dict with:
            - coverage_pct: float (0-100)
            - coverage_category: str ("0-10%" / "10-20%" / "20-30%" / "30%+")
            - contours: list of contour point arrays (for overlay rendering)
            - mask: np.ndarray binary mask of pigmented regions
            - ita_angle: float (Individual Typology Angle — melanin estimate)
    """
    h, w = image_rgb.shape[:2]

    # Convert to LAB color space
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_channel = lab[:, :, 0].astype(np.float32)
    b_channel = lab[:, :, 2].astype(np.float32)

    # ─── ITA Angle (melanin baseline estimation) ───
    ita_angle = _compute_ita(l_channel, b_channel, face_mask)

    # ─── Hyperpigmentation detection ───
    # Compute local mean brightness
    blur_size = max(51, (min(h, w) // 8) | 1)  # Ensure odd
    local_mean = cv2.GaussianBlur(l_channel, (blur_size, blur_size), 0)

    # Dark regions: significantly darker than local average
    # Adaptive threshold based on skin tone (ITA)
    if ita_angle > 55:
        # Very light skin — more sensitive threshold
        threshold = 12
    elif ita_angle > 28:
        # Medium skin
        threshold = 18
    else:
        # Darker skin — higher threshold to avoid false positives
        threshold = 25

    diff = local_mean - l_channel
    dark_mask = (diff > threshold).astype(np.uint8) * 255

    # Apply face mask
    if face_mask is not None:
        dark_mask = cv2.bitwise_and(dark_mask, face_mask)

    # Morphological cleanup
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

    # Remove noise
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel_small)
    # Fill small holes
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel_large)

    # Filter by size — remove very small or very large regions
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = []
    clean_mask = np.zeros_like(dark_mask)

    min_area = (h * w) * 0.0005  # Min 0.05% of image
    max_area = (h * w) * 0.15  # Max 15% of image

    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area < area < max_area:
            valid_contours.append(contour)
            cv2.fillPoly(clean_mask, [contour], 255)

    # Calculate coverage percentage
    if face_mask is not None:
        face_area = np.sum(face_mask > 0)
    else:
        face_area = h * w

    pigmented_area = np.sum(clean_mask > 0)
    coverage_pct = round((pigmented_area / max(face_area, 1)) * 100, 1)

    # Categorize
    if coverage_pct < 10:
        category = "0-10%"
    elif coverage_pct < 20:
        category = "10-20%"
    elif coverage_pct < 30:
        category = "20-30%"
    else:
        category = "30%+"

    # Convert contours to serializable format
    contour_points = []
    for contour in valid_contours:
        points = contour.squeeze().tolist()
        if isinstance(points[0], list):
            contour_points.append(points)
        else:
            contour_points.append([points])

    return {
        "coverage_pct": coverage_pct,
        "coverage_category": category,
        "contours": contour_points,
        "mask": clean_mask,
        "ita_angle": round(ita_angle, 1),
    }


def _compute_ita(
    l_channel: np.ndarray,
    b_channel: np.ndarray,
    face_mask: Optional[np.ndarray] = None,
) -> float:
    """
    Compute Individual Typology Angle (ITA) for melanin estimation.
    ITA = arctan((L - 50) / b) × (180 / π)

    Higher ITA = lighter skin; Lower ITA = darker skin
    Reference scale:
        > 55°: Very light
        41-55°: Light
        28-41°: Intermediate
        10-28°: Tan
        < 10°: Dark
    """
    if face_mask is not None:
        mask_bool = face_mask > 0
        l_vals = l_channel[mask_bool]
        b_vals = b_channel[mask_bool]
    else:
        l_vals = l_channel.flatten()
        b_vals = b_channel.flatten()

    if len(l_vals) == 0:
        return 30.0  # Default intermediate

    l_mean = np.mean(l_vals)
    b_mean = np.mean(b_vals)

    # Avoid division by zero
    if abs(b_mean) < 0.01:
        b_mean = 0.01

    # ITA formula (L is 0-255 in OpenCV, normalize to 0-100 for formula)
    l_normalized = (l_mean / 255.0) * 100.0
    b_normalized = (b_mean / 255.0) * 100.0 - 50.0  # Center b around 0

    ita = np.arctan2(l_normalized - 50, b_normalized) * (180.0 / np.pi)

    return float(ita)
