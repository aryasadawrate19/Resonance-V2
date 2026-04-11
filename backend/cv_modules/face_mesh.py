"""
Face Mesh — MediaPipe FaceLandmarker (Tasks API) for 5-zone segmentation.
Step 2 of the CV pipeline.

Compatible with mediapipe >= 0.10.9 (Tasks API).
Falls back to Haar Cascade if MediaPipe is unavailable.
"""

import os
import numpy as np
import cv2
import logging
import urllib.request

logger = logging.getLogger(__name__)

# Path to store the FaceLandmarker model bundle
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

# ─── Zone landmark index groups (MediaPipe 478 landmarks) ───
# Simplified zone polygons using key boundary landmarks for face segmentation.
ZONE_SIMPLE = {
    "forehead": [10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58,
                 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379,
                 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338],
    "left_cheek": [93, 132, 174, 135, 169, 170, 140, 171, 175, 396,
                   395, 369, 370, 462, 250, 309, 392, 289, 356, 454],
    "right_cheek": [234, 127, 162, 21, 54, 103, 67, 109, 10, 338,
                    297, 332, 284, 251, 389],
    "nose": [168, 6, 197, 195, 5, 4, 1, 19, 94, 2, 164,
             0, 267, 269, 270, 409, 291, 375, 321, 405,
             314, 17, 84, 181, 91, 146, 61, 185, 40, 39, 37],
    "chin_jawline": [152, 377, 400, 378, 379, 365, 397, 288, 361,
                     323, 454, 356, 389, 251, 284, 332, 297, 338,
                     10, 109, 67, 103, 54, 21, 162, 127, 234,
                     93, 132, 58, 172, 136, 150, 149, 176, 148],
}

# Face oval indices for mask creation
FACE_OVAL_INDICES = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
]


def _download_model():
    """Download the FaceLandmarker model bundle if not already present."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
        return True

    logger.info(f"Downloading FaceLandmarker model to {MODEL_PATH} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        logger.info(f"FaceLandmarker model downloaded ({os.path.getsize(MODEL_PATH)} bytes)")
        return True
    except Exception as e:
        logger.error(f"Failed to download FaceLandmarker model: {e}")
        return False


class FaceMeshAnalyzer:
    """MediaPipe FaceLandmarker for facial zone segmentation."""

    def __init__(self):
        self._landmarker = None
        self._face_cascade = None
        self._mp_available = None  # None = not yet checked

    def _load_mediapipe(self):
        """Lazy load MediaPipe FaceLandmarker (Tasks API)."""
        if self._mp_available is not None:
            return  # Already attempted

        try:
            import mediapipe as mp

            # Download the model bundle if needed
            if not _download_model():
                raise RuntimeError("FaceLandmarker model not available")

            # Create the FaceLandmarker using the new Tasks API
            BaseOptions = mp.tasks.BaseOptions
            FaceLandmarker = mp.tasks.vision.FaceLandmarker
            FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
            RunningMode = mp.tasks.vision.RunningMode

            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.3,
                min_face_presence_confidence=0.3,
                min_tracking_confidence=0.3,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )

            self._landmarker = FaceLandmarker.create_from_options(options)
            self._mp_available = True
            logger.info("MediaPipe FaceLandmarker loaded successfully (Tasks API)")

        except Exception as e:
            logger.warning(f"MediaPipe FaceLandmarker unavailable: {e}. Using Haar Cascade fallback.")
            self._landmarker = None
            self._mp_available = False

    def _load_haar_cascade(self):
        """Load OpenCV Haar Cascade as fallback."""
        if self._face_cascade is None:
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

    def analyze(self, image_rgb: np.ndarray) -> dict:
        """
        Detect face landmarks and extract zone polygons.

        Returns:
            dict with:
                - landmarks: list of (x, y) pixel coordinates (478 points) or None
                - zones: dict of zone_name → list of (x, y) polygon points
                - face_bbox: [x1, y1, x2, y2] face bounding box
                - face_detected: bool
                - face_mask: np.ndarray binary mask of face region
        """
        if self._mp_available is None:
            self._load_mediapipe()

        h, w = image_rgb.shape[:2]
        logger.info(f"Face analysis input: {w}×{h}, dtype={image_rgb.dtype}, shape={image_rgb.shape}")

        # Try MediaPipe FaceLandmarker
        if self._landmarker is not None:
            try:
                import mediapipe as mp

                # FaceLandmarker needs faces to be at least ~100px wide.
                # Upscale small images, downscale large ones.
                MIN_DIM = 640
                MAX_DIM = 1024
                detect_img = image_rgb

                if max(h, w) < MIN_DIM:
                    # Image too small — upscale for reliable detection
                    scale_factor = MIN_DIM / max(h, w)
                    new_w = int(w * scale_factor)
                    new_h = int(h * scale_factor)
                    detect_img = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                    logger.info(f"Upscaled for detection: {w}×{h} → {new_w}×{new_h}")
                elif max(h, w) > MAX_DIM:
                    # Image too large — downscale for performance
                    scale_factor = MAX_DIM / max(h, w)
                    new_w = int(w * scale_factor)
                    new_h = int(h * scale_factor)
                    detect_img = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                    logger.info(f"Downscaled for detection: {w}×{h} → {new_w}×{new_h}")

                # Ensure array is contiguous C-order uint8 RGB
                detect_img = np.ascontiguousarray(detect_img, dtype=np.uint8)

                # Convert numpy array to MediaPipe Image
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=detect_img,
                )

                result = self._landmarker.detect(mp_image)

                logger.info(f"FaceLandmarker result: {len(result.face_landmarks)} face(s) found")

                if result.face_landmarks and len(result.face_landmarks) > 0:
                    face_lm = result.face_landmarks[0]

                    # Map landmarks back to original image coordinates
                    # FaceLandmarker returns normalized [0,1] coordinates,
                    # so we multiply by the ORIGINAL dimensions, not the detection dims
                    landmarks = [
                        (int(lm.x * w), int(lm.y * h))
                        for lm in face_lm
                    ]

                    zones = self._extract_zones(landmarks)
                    face_bbox = self._landmarks_to_bbox(landmarks, w, h)
                    face_mask = self._create_face_mask(landmarks, w, h)

                    logger.info(f"Face detected with {len(landmarks)} landmarks")
                    return {
                        "landmarks": landmarks,
                        "zones": zones,
                        "face_bbox": face_bbox,
                        "face_detected": True,
                        "face_mask": face_mask,
                    }
                else:
                    logger.info("FaceLandmarker returned 0 faces")

            except Exception as e:
                logger.warning(f"FaceLandmarker inference failed: {e}", exc_info=True)

        # Fallback to Haar Cascade
        logger.info("Falling back to Haar Cascade face detection")
        return self._haar_fallback(image_rgb)

    def _extract_zones(self, landmarks: list) -> dict:
        """Extract zone polygons from MediaPipe landmarks."""
        zones = {}
        for zone_name, indices in ZONE_SIMPLE.items():
            valid_indices = [i for i in indices if i < len(landmarks)]
            if valid_indices:
                points = [landmarks[i] for i in valid_indices]
                zones[zone_name] = points
            else:
                zones[zone_name] = []
        return zones

    def _landmarks_to_bbox(self, landmarks: list, w: int, h: int) -> list:
        """Compute face bounding box from landmarks."""
        xs = [p[0] for p in landmarks]
        ys = [p[1] for p in landmarks]
        x1 = max(0, min(xs) - 10)
        y1 = max(0, min(ys) - 10)
        x2 = min(w, max(xs) + 10)
        y2 = min(h, max(ys) + 10)
        return [x1, y1, x2, y2]

    def _create_face_mask(self, landmarks: list, w: int, h: int) -> np.ndarray:
        """Create a binary mask of the face region."""
        mask = np.zeros((h, w), dtype=np.uint8)
        valid = [i for i in FACE_OVAL_INDICES if i < len(landmarks)]
        if valid:
            points = np.array([landmarks[i] for i in valid], dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
        return mask

    def _haar_fallback(self, image_rgb: np.ndarray) -> dict:
        """Haar Cascade fallback when MediaPipe is unavailable."""
        self._load_haar_cascade()
        h, w = image_rgb.shape[:2]

        # Upscale small images for better Haar detection
        detect_img = image_rgb
        scale = 1.0
        if max(h, w) < 400:
            scale = 400 / max(h, w)
            detect_img = cv2.resize(image_rgb, (int(w * scale), int(h * scale)),
                                    interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(detect_img, cv2.COLOR_RGB2GRAY)

        # Try progressively more permissive detection
        faces = []
        for min_neighbors in [4, 3, 2]:
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=min_neighbors, minSize=(30, 30)
            )
            if len(faces) > 0:
                logger.info(f"Haar cascade found {len(faces)} face(s) (minNeighbors={min_neighbors})")
                break

        if len(faces) > 0:
            fx, fy, fw, fh = faces[0]
            # Map back to original coordinates if we upscaled
            face_bbox = [int(fx / scale), int(fy / scale),
                         int((fx + fw) / scale), int((fy + fh) / scale)]
            face_detected = True
        else:
            # No face detected — use center 70% of the image as face region
            logger.info("No face found by Haar cascade, using center region estimate")
            margin_x = int(w * 0.15)
            margin_y = int(h * 0.1)
            face_bbox = [margin_x, margin_y, w - margin_x, h - margin_y]
            face_detected = False

        # Create approximate zone regions from face bbox
        x1, y1, x2, y2 = face_bbox
        face_w = x2 - x1
        face_h = y2 - y1

        zones = {
            "forehead": self._rect_to_poly(x1, y1, x2, y1 + face_h // 4),
            "left_cheek": self._rect_to_poly(x1, y1 + face_h // 4, x1 + face_w // 2, y1 + 3 * face_h // 4),
            "right_cheek": self._rect_to_poly(x1 + face_w // 2, y1 + face_h // 4, x2, y1 + 3 * face_h // 4),
            "nose": self._rect_to_poly(x1 + face_w // 3, y1 + face_h // 4, x1 + 2 * face_w // 3, y1 + 3 * face_h // 4),
            "chin_jawline": self._rect_to_poly(x1, y1 + 3 * face_h // 4, x2, y2),
        }

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255

        return {
            "landmarks": None,
            "zones": zones,
            "face_bbox": face_bbox,
            "face_detected": face_detected,
            "face_mask": mask,
        }

    @staticmethod
    def _rect_to_poly(x1, y1, x2, y2) -> list:
        """Convert rectangle to polygon points."""
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


# Module-level singleton
_analyzer = None

def get_face_mesh_analyzer() -> FaceMeshAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = FaceMeshAnalyzer()
    return _analyzer
