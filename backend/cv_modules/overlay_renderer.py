"""
Overlay Renderer — Server-side annotated image composition using Pillow.
Composites all CV pipeline outputs onto the original uploaded photo.
"""

import io
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Color palette per PRD spec ───
COLORS = {
    "comedonal": (34, 197, 94),       # #22C55E green
    "inflammatory": (239, 68, 68),     # #EF4444 red
    "other": (59, 130, 246),           # #3B82F6 blue
    "pigmentation_mild": (249, 115, 22),   # #F97316 orange
    "pigmentation_severe": (185, 28, 28),  # #B91C1C dark red
    "mesh": (34, 197, 94),             # #22C55E green
}

ZONE_COLORS = {
    "forehead": (59, 130, 246, 50),     # Blue, 20% opacity
    "left_cheek": (168, 85, 247, 50),   # Purple
    "right_cheek": (236, 72, 153, 50),  # Pink
    "nose": (34, 197, 94, 50),          # Green
    "chin_jawline": (245, 158, 11, 50), # Amber
}

SEVERITY_BADGE_COLORS = {
    "Clear": (34, 197, 94),
    "Mild": (245, 158, 11),
    "Moderate": (249, 115, 22),
    "Severe": (239, 68, 68),
}


def render_overlays(
    original_pil: Image.Image,
    lesions: list,
    zones: dict,
    pigmentation_contours: list,
    pigmentation_coverage: float,
    severity: str,
    landmarks: Optional[list] = None,
    skin_health_score: Optional[int] = None,
) -> str:
    """
    Compose all overlay layers onto the original image.

    Layer order:
    1. Original image (base)
    2. Zone segmentation (translucent fills)
    3. Face mesh wireframe (if landmarks available)
    4. Lesion bounding boxes (color-coded)
    5. Hyperpigmentation outlines
    6. Severity badge

    Returns:
        Base64-encoded PNG string.
    """
    # Work on a copy
    img = original_pil.copy().convert("RGBA")
    w, h = img.size

    # Create overlay layer for transparent elements
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # ─── Layer 1: Zone segmentation fills ───
    _draw_zones(draw_overlay, zones, w, h)

    # Composite zone overlay
    img = Image.alpha_composite(img, overlay)

    # ─── Layer 2: Face mesh wireframe ───
    if landmarks:
        mesh_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        _draw_mesh(mesh_overlay, landmarks)
        img = Image.alpha_composite(img, mesh_overlay)

    # Convert to RGB for further drawing
    img_rgb = img.convert("RGB")
    draw = ImageDraw.Draw(img_rgb)

    # Load font (use default if custom not available)
    font = _get_font(12)
    font_large = _get_font(16)
    font_badge = _get_font(20)

    # ─── Layer 3: Lesion bounding boxes ───
    _draw_lesions(draw, lesions, font)

    # ─── Layer 4: Hyperpigmentation outlines ───
    _draw_pigmentation(draw, pigmentation_contours, pigmentation_coverage)

    # ─── Layer 5: Severity badge ───
    _draw_severity_badge(draw, severity, w, h, font_badge)

    # ─── Layer 6: Score indicator (bottom-left) ───
    if skin_health_score is not None:
        _draw_score_indicator(draw, skin_health_score, w, h, font_large)

    # Encode to base64
    buffer = io.BytesIO()
    img_rgb.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _draw_zones(draw: ImageDraw.Draw, zones: dict, w: int, h: int):
    """Draw translucent zone polygons."""
    for zone_name, points in zones.items():
        if not points or len(points) < 3:
            continue

        color = ZONE_COLORS.get(zone_name, (128, 128, 128, 50))

        # Convert points to tuples
        poly_points = [(int(p[0]), int(p[1])) for p in points]

        try:
            draw.polygon(poly_points, fill=color, outline=(*color[:3], 100))
        except Exception as e:
            logger.debug(f"Failed to draw zone {zone_name}: {e}")


def _draw_mesh(mesh_img: Image.Image, landmarks: list):
    """Draw face mesh wireframe."""
    draw = ImageDraw.Draw(mesh_img)
    color = (*COLORS["mesh"], 76)  # 30% opacity

    # Draw connections between nearby landmarks
    # Use Delaunay-like connections for a mesh look
    n = len(landmarks)
    step = max(1, n // 100)  # Reduce density for visual clarity

    for i in range(0, n, step):
        x1, y1 = landmarks[i]
        # Connect to nearby landmarks
        for j in range(i + 1, min(i + 5, n)):
            x2, y2 = landmarks[j]
            dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            if dist < 30:
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

        # Draw landmark dots
        draw.ellipse(
            [(x1 - 1, y1 - 1), (x1 + 1, y1 + 1)],
            fill=(*COLORS["mesh"], 50),
        )


def _draw_lesions(draw: ImageDraw.Draw, lesions: list, font):
    """Draw color-coded lesion bounding boxes with ID labels."""
    for lesion in lesions:
        bbox = lesion["bbox"]
        x1, y1, x2, y2 = bbox
        type_hint = lesion.get("type_hint", "other")
        lesion_id = lesion.get("id", "?")
        conf = lesion.get("confidence", 0)

        color = COLORS.get(type_hint, COLORS["other"])

        # Draw bounding box (2px border per PRD)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

        # Draw ID label background
        label_text = f"{lesion_id}"
        label_bbox = draw.textbbox((x1, y1 - 16), label_text, font=font)
        label_w = label_bbox[2] - label_bbox[0]
        label_h = label_bbox[3] - label_bbox[1]

        draw.rectangle(
            [x1, y1 - label_h - 6, x1 + label_w + 8, y1],
            fill=color,
        )
        draw.text(
            (x1 + 4, y1 - label_h - 4),
            label_text,
            fill=(255, 255, 255),
            font=font,
        )


def _draw_pigmentation(draw: ImageDraw.Draw, contours: list, coverage: float):
    """Draw hyperpigmentation boundary outlines."""
    color = COLORS["pigmentation_mild"] if coverage < 20 else COLORS["pigmentation_severe"]

    for contour in contours:
        if len(contour) < 3:
            continue

        points = [(int(p[0]), int(p[1])) for p in contour]

        try:
            # Draw outline (1.5px → use width=2)
            draw.polygon(points, outline=color)
            # Draw slightly thicker outline
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                draw.line([p1, p2], fill=color, width=2)
        except Exception:
            pass


def _draw_severity_badge(draw: ImageDraw.Draw, severity: str, w: int, h: int, font):
    """Draw severity badge in top-right corner."""
    badge_color = SEVERITY_BADGE_COLORS.get(severity, (128, 128, 128))

    text = f"  {severity.upper()}  "
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    padding = 8
    badge_x = w - text_w - padding * 2 - 16
    badge_y = 16

    # Background
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + text_w + padding * 2, badge_y + text_h + padding * 2],
        radius=6,
        fill=badge_color,
    )

    # Text
    draw.text(
        (badge_x + padding, badge_y + padding),
        text,
        fill=(255, 255, 255),
        font=font,
    )


def _draw_score_indicator(draw: ImageDraw.Draw, score: int, w: int, h: int, font):
    """Draw skin health score in bottom-left."""
    text = f"Score: {score}/100"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    padding = 6
    x = 16
    y = h - text_h - padding * 2 - 16

    # Semi-transparent background
    draw.rounded_rectangle(
        [x, y, x + text_w + padding * 2, y + text_h + padding * 2],
        radius=4,
        fill=(0, 0, 0, 180) if hasattr(draw, '_image') else (0, 0, 0),
    )
    draw.text((x + padding, y + padding), text, fill=(255, 255, 255), font=font)


def _get_font(size: int):
    """Get a font, falling back to default if custom fonts aren't available."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()
