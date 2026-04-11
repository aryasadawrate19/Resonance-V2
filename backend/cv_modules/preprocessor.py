"""
Image Preprocessor — EXIF correction, resize, normalize.
Step 1 of the CV pipeline.
"""

import io
import numpy as np
from PIL import Image, ImageOps
import cv2


def preprocess_image(image_bytes: bytes, target_size: int = 640) -> dict:
    """
    Preprocess uploaded image for the CV pipeline.

    Returns:
        dict with:
            - original_pil: PIL Image (original size, EXIF corrected)
            - original_np: numpy array (original size, RGB)
            - processed_np: numpy array (resized to target_size, RGB)
            - original_width: int
            - original_height: int
            - scale_x: float (original/processed width ratio)
            - scale_y: float (original/processed height ratio)
    """
    # Load image from bytes
    pil_image = Image.open(io.BytesIO(image_bytes))

    # Apply EXIF orientation correction
    pil_image = ImageOps.exif_transpose(pil_image)

    # Convert to RGB (handles RGBA, grayscale, etc.)
    pil_image = pil_image.convert("RGB")

    original_width, original_height = pil_image.size

    # Convert to numpy (RGB)
    original_np = np.array(pil_image)

    # Resize with aspect ratio preservation + padding
    processed_np = _resize_with_padding(original_np, target_size)

    # Calculate scale factors for coordinate mapping
    scale_x = original_width / target_size
    scale_y = original_height / target_size

    return {
        "original_pil": pil_image,
        "original_np": original_np,
        "processed_np": processed_np,
        "original_width": original_width,
        "original_height": original_height,
        "scale_x": scale_x,
        "scale_y": scale_y,
    }


def _resize_with_padding(image: np.ndarray, target_size: int) -> np.ndarray:
    """Resize image to target_size × target_size with letterboxing."""
    h, w = image.shape[:2]

    # Calculate scale to fit within target_size
    scale = min(target_size / w, target_size / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Create padded canvas
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)

    # Center the resized image
    y_offset = (target_size - new_h) // 2
    x_offset = (target_size - new_w) // 2
    canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized

    return canvas


def validate_image(image_bytes: bytes) -> tuple[bool, str]:
    """Validate uploaded image is suitable for analysis."""
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        w, h = pil_image.size

        if w < 100 or h < 100:
            return False, "Image too small. Please upload at least 100×100 pixels."

        if w > 8000 or h > 8000:
            return False, "Image too large. Maximum 8000×8000 pixels."

        if pil_image.mode not in ("RGB", "RGBA", "L"):
            return False, "Unsupported image format."

        return True, "OK"

    except Exception:
        return False, "Could not read image file. Please upload a valid JPEG or PNG."
