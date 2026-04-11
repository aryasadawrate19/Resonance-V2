"""
Lesion Detector — YOLOv8 (acne-specific) or OpenCV fallback.
Step 3 of the CV pipeline — spatial detection only, classification handled by hybrid_model.
"""

import os
import numpy as np
import cv2
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


class LesionDetector:
    """Detect skin lesions using YOLOv8 or OpenCV fallback."""

    def __init__(self):
        self._yolo_model = None
        self._yolo_checked = False

    def _try_load_yolo(self):
        """Attempt to load acne-specific YOLOv8 weights."""
        if self._yolo_checked:
            return

        self._yolo_checked = True
        acne_model_path = os.path.join(MODELS_DIR, "acne_yolov8.pt")

        if os.path.exists(acne_model_path):
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO(acne_model_path)
                logger.info(f"Loaded acne-specific YOLOv8 from {acne_model_path}")
            except Exception as e:
                logger.warning(f"Failed to load YOLOv8: {e}")
                self._yolo_model = None
        else:
            logger.info("No acne-specific YOLO weights found. Using OpenCV fallback.")

    def detect(self, image_rgb: np.ndarray, face_mask: Optional[np.ndarray] = None) -> list:
        """
        Detect lesions in the image.

        Args:
            image_rgb: RGB image as numpy array
            face_mask: Optional binary mask of face region

        Returns:
            List of lesion dicts: [{id, bbox:[x1,y1,x2,y2], confidence, type_hint}]
        """
        self._try_load_yolo()

        if self._yolo_model is not None:
            return self._yolo_detect(image_rgb, face_mask)
        return self._opencv_detect(image_rgb, face_mask)

    def _yolo_detect(self, image_rgb: np.ndarray, face_mask: Optional[np.ndarray]) -> list:
        """YOLOv8 inference for lesion detection."""
        results = self._yolo_model(image_rgb, verbose=False)
        lesions = []

        for i, box in enumerate(results[0].boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            # Map YOLO class to type hint
            cls_names = results[0].names
            cls_name = cls_names.get(cls_id, "other")

            # Type hint mapping
            if "inflam" in cls_name.lower() or "papule" in cls_name.lower() or "pustule" in cls_name.lower():
                type_hint = "inflammatory"
            elif "comedo" in cls_name.lower() or "blackhead" in cls_name.lower() or "whitehead" in cls_name.lower():
                type_hint = "comedonal"
            else:
                type_hint = "other"

            lesions.append({
                "id": f"L{i + 1:03d}",
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "confidence": round(conf, 3),
                "type_hint": type_hint,
            })

        return lesions

    def _opencv_detect(self, image_rgb: np.ndarray, face_mask: Optional[np.ndarray]) -> list:
        """
        OpenCV-based lesion detection fallback.
        Multi-method approach using HSV redness, LAB color deviation,
        and texture analysis to detect inflammatory and comedonal lesions.
        """
        h, w = image_rgb.shape[:2]
        img_area = h * w
        lesions = []

        # Upscale small images for better morphological operations
        scale = 1.0
        proc_img = image_rgb
        proc_mask = face_mask

        if max(h, w) < 400:
            scale = 400 / max(h, w)
            proc_img = cv2.resize(image_rgb, (int(w * scale), int(h * scale)),
                                  interpolation=cv2.INTER_CUBIC)
            if face_mask is not None:
                proc_mask = cv2.resize(face_mask, (int(w * scale), int(h * scale)),
                                       interpolation=cv2.INTER_NEAREST)
            ph, pw = proc_img.shape[:2]
        else:
            ph, pw = h, w

        proc_area = ph * pw

        # Create face-only region
        if proc_mask is not None:
            masked_image = cv2.bitwise_and(proc_img, proc_img, mask=proc_mask)
        else:
            masked_image = proc_img.copy()

        # Adaptive kernel size based on image dimensions
        ksize = max(3, min(5, min(ph, pw) // 50))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))

        # ─── Method 1: Inflammatory lesions (redness in HSV) ───
        hsv = cv2.cvtColor(masked_image, cv2.COLOR_RGB2HSV)

        # Broader red detection — lower saturation for pinkish/diffuse redness
        lower_red1 = np.array([0, 25, 40])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([155, 25, 40])
        upper_red2 = np.array([180, 255, 255])

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask_red1 | mask_red2

        if proc_mask is not None:
            red_mask = cv2.bitwise_and(red_mask, proc_mask)

        # Light morphological cleanup
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            min_area = proc_area * 0.0002
            max_area = proc_area * 0.06

            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(contour)
                aspect = max(bw, bh) / (min(bw, bh) + 1)
                if aspect < 5:
                    lesions.append({
                        "bbox": [int(x / scale), int(y / scale),
                                 int((x + bw) / scale), int((y + bh) / scale)],
                        "confidence": round(min(0.7, area / (max_area * 0.3)), 3),
                        "type_hint": "inflammatory",
                    })

        # ─── Method 2: Redness via LAB a-channel (pink/red skin) ───
        lab = cv2.cvtColor(masked_image, cv2.COLOR_RGB2LAB)
        a_channel = lab[:, :, 1]  # a-channel: positive = red/pink

        # Regions significantly more red than the mean
        a_mean = np.mean(a_channel[proc_mask > 0]) if proc_mask is not None else np.mean(a_channel)
        a_std = np.std(a_channel[proc_mask > 0]) if proc_mask is not None else np.std(a_channel)
        red_threshold = a_mean + max(a_std * 1.2, 5)

        lab_red_mask = (a_channel > red_threshold).astype(np.uint8) * 255

        if proc_mask is not None:
            lab_red_mask = cv2.bitwise_and(lab_red_mask, proc_mask)

        # Remove areas already found by HSV
        lab_red_mask = cv2.bitwise_and(lab_red_mask, cv2.bitwise_not(red_mask))

        lab_red_mask = cv2.morphologyEx(lab_red_mask, cv2.MORPH_CLOSE, kernel)
        lab_red_mask = cv2.morphologyEx(lab_red_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(lab_red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            min_area = proc_area * 0.0002
            max_area = proc_area * 0.05

            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(contour)
                aspect = max(bw, bh) / (min(bw, bh) + 1)
                if aspect < 5:
                    lesions.append({
                        "bbox": [int(x / scale), int(y / scale),
                                 int((x + bw) / scale), int((y + bh) / scale)],
                        "confidence": round(min(0.6, area / (max_area * 0.5)), 3),
                        "type_hint": "inflammatory",
                    })

        # ─── Method 3: Comedonal lesions (dark spots via adaptive L-channel) ───
        l_channel = lab[:, :, 0]

        # Local mean comparison with smaller kernel for finer detail
        blur_ksize = max(21, (min(ph, pw) // 8) | 1)  # Ensure odd
        blur = cv2.GaussianBlur(l_channel, (blur_ksize, blur_ksize), 0)
        diff = blur.astype(np.float32) - l_channel.astype(np.float32)

        # Comedonal: darker than local average by adaptive margin
        dark_threshold = max(8, a_std * 0.8)  # Lower threshold for subtle spots
        dark_mask = (diff > dark_threshold).astype(np.uint8) * 255

        if proc_mask is not None:
            dark_mask = cv2.bitwise_and(dark_mask, proc_mask)

        # Remove inflammatory areas already found
        all_inflam = red_mask | lab_red_mask
        dark_mask = cv2.bitwise_and(dark_mask, cv2.bitwise_not(all_inflam))

        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel)
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            min_area = proc_area * 0.00015
            max_area = proc_area * 0.03

            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(contour)
                aspect = max(bw, bh) / (min(bw, bh) + 1)
                if aspect < 4:
                    lesions.append({
                        "bbox": [int(x / scale), int(y / scale),
                                 int((x + bw) / scale), int((y + bh) / scale)],
                        "confidence": round(min(0.5, area / (max_area * 0.5)), 3),
                        "type_hint": "comedonal",
                    })

        # ─── Method 4: Texture roughness (bumps visible in this image) ───
        gray = cv2.cvtColor(proc_img, cv2.COLOR_RGB2GRAY)
        if proc_mask is not None:
            gray = cv2.bitwise_and(gray, proc_mask)

        # Laplacian highlights edges/bumps
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_abs = np.abs(laplacian).astype(np.uint8)

        lap_mean = np.mean(laplacian_abs[proc_mask > 0]) if proc_mask is not None else np.mean(laplacian_abs)
        lap_std = np.std(laplacian_abs[proc_mask > 0]) if proc_mask is not None else np.std(laplacian_abs)
        texture_threshold = lap_mean + max(lap_std * 2, 15)

        texture_mask = (laplacian_abs > texture_threshold).astype(np.uint8) * 255

        if proc_mask is not None:
            texture_mask = cv2.bitwise_and(texture_mask, proc_mask)

        # Dilate to merge nearby texture spots into clusters
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize + 2, ksize + 2))
        texture_mask = cv2.dilate(texture_mask, dilate_kernel, iterations=2)
        texture_mask = cv2.morphologyEx(texture_mask, cv2.MORPH_CLOSE, dilate_kernel)

        # Remove already detected areas
        all_found = all_inflam | dark_mask
        texture_mask = cv2.bitwise_and(texture_mask, cv2.bitwise_not(all_found))

        contours, _ = cv2.findContours(texture_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            min_area = proc_area * 0.0003
            max_area = proc_area * 0.04

            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(contour)
                aspect = max(bw, bh) / (min(bw, bh) + 1)
                if aspect < 5:
                    lesions.append({
                        "bbox": [int(x / scale), int(y / scale),
                                 int((x + bw) / scale), int((y + bh) / scale)],
                        "confidence": round(min(0.45, area / (max_area * 0.5)), 3),
                        "type_hint": "other",
                    })

        # De-duplicate overlapping detections
        lesions = self._nms(lesions, iou_threshold=0.4)

        # Assign IDs, sort by confidence
        lesions.sort(key=lambda l: l["confidence"], reverse=True)
        for i, l in enumerate(lesions):
            l["id"] = f"L{i + 1:03d}"

        logger.info(f"OpenCV detected {len(lesions)} lesions "
                    f"(inflam={sum(1 for l in lesions if l['type_hint'] == 'inflammatory')}, "
                    f"comedonal={sum(1 for l in lesions if l['type_hint'] == 'comedonal')}, "
                    f"texture={sum(1 for l in lesions if l['type_hint'] == 'other')})")

        # Cap at reasonable maximum
        return lesions[:40]

    @staticmethod
    def _nms(lesions: list, iou_threshold: float = 0.4) -> list:
        """Simple Non-Maximum Suppression to remove overlapping detections."""
        if not lesions:
            return []

        # Sort by confidence descending
        sorted_lesions = sorted(lesions, key=lambda l: l["confidence"], reverse=True)
        keep = []

        for candidate in sorted_lesions:
            is_duplicate = False
            for kept in keep:
                iou = _compute_iou(candidate["bbox"], kept["bbox"])
                if iou > iou_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                keep.append(candidate)

        return keep

    @staticmethod
    def crop_lesion(image: np.ndarray, bbox: list) -> np.ndarray:
        """Correctly crop a lesion region from the image."""
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        # Clamp to image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        return image[y1:y2, x1:x2]


def _compute_iou(box1: list, box2: list) -> float:
    """Compute Intersection over Union for two bboxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / max(union, 1e-6)


# Module-level singleton
_detector = None

def get_lesion_detector() -> LesionDetector:
    global _detector
    if _detector is None:
        _detector = LesionDetector()
    return _detector
