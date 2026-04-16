"""
Hybrid Model — Hugging Face Transformers integration + fusion logic.
Combines YOLOv8 spatial detection with HF semantic classification.

Primary HF model: imfarzanansari/skintelligent-acne
"""

import os
import logging
import numpy as np
from PIL import Image
from typing import Optional

logger = logging.getLogger(__name__)

# Severity mapping from model labels to our system
SEVERITY_MAP = {
    "level_0": "Clear",
    "level_1": "Mild",
    "level_2": "Moderate",
    "level_3": "Severe",
    "clear": "Clear",
    "mild": "Mild",
    "moderate": "Moderate",
    "severe": "Severe",
    "0": "Clear",
    "1": "Mild",
    "2": "Moderate",
    "3": "Severe",
}


class HybridSkinAnalyzer:
    """
    Singleton hybrid AI analyzer combining:
    - Hugging Face Transformers (semantic classification — primary)
    - YOLOv8/OpenCV (spatial detection — supporting)

    The HF model is the primary source of truth for severity.
    Lesion count provides guard-rail adjustments only.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._hf_pipeline = None
            cls._instance._hf_loaded = False
            cls._instance._hf_failed = False
            cls._instance._device = None
        return cls._instance

    def _detect_device(self) -> str:
        """Detect best available device (GPU → CPU)."""
        if self._device is not None:
            return self._device

        try:
            import torch
            if torch.cuda.is_available():
                self._device = "cuda"
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self._device = "cpu"
                logger.info("Using CPU (no GPU detected)")
        except ImportError:
            self._device = "cpu"
            logger.info("PyTorch not available, using CPU")

        return self._device

    def _load_hf_classifier(self):
        """Lazy load the HF classification pipeline on first use."""
        if self._hf_loaded or self._hf_failed:
            return

        try:
            from transformers import pipeline as hf_pipeline

            device = self._detect_device()
            device_arg = 0 if device == "cuda" else -1

            # Get HuggingFace token for authenticated model access
            hf_token = os.getenv("HF_TOKEN")
            if hf_token and hf_token != "your_huggingface_token_here":
                logger.info("Using HF_TOKEN for authenticated model access")
            else:
                hf_token = None
                logger.info("No HF_TOKEN set — attempting public model access")

            logger.info("Loading HF model: imfarzanansari/skintelligent-acne ...")
            self._hf_pipeline = hf_pipeline(
                "image-classification",
                model="imfarzanansari/skintelligent-acne",
                device=device_arg,
                token=hf_token,
            )
            self._hf_loaded = True
            logger.info("HF classification model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load HF model: {e}")
            self._hf_failed = True
            self._hf_pipeline = None

    def classify_global_severity(self, pil_image: Image.Image) -> dict:
        """
        Run HF model on FULL face image for global severity classification.
        This is the PRIMARY source of truth.

        Returns:
            {
                "severity": str ("Clear"/"Mild"/"Moderate"/"Severe"),
                "confidence": float (0-1),
                "probabilities": dict (severity → probability),
                "source": str ("hf_model" or "fallback")
            }
        """
        self._load_hf_classifier()

        if self._hf_pipeline is not None:
            try:
                # Ensure image is RGB and reasonable size
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")

                results = self._hf_pipeline(pil_image)

                # Parse results
                probabilities = {}
                best_label = None
                best_score = 0.0

                for item in results:
                    label = item["label"].lower().strip()
                    score = item["score"]

                    # Map to our severity levels
                    severity = SEVERITY_MAP.get(label, None)
                    if severity:
                        probabilities[severity] = round(score, 4)
                        if score > best_score:
                            best_score = score
                            best_label = severity
                    else:
                        # Try to infer from label text
                        for key, val in SEVERITY_MAP.items():
                            if key in label:
                                probabilities[val] = round(score, 4)
                                if score > best_score:
                                    best_score = score
                                    best_label = val
                                break

                if best_label is None:
                    # Model returned unknown labels
                    best_label = "Moderate"
                    best_score = 0.5

                return {
                    "severity": best_label,
                    "confidence": round(best_score, 4),
                    "probabilities": probabilities,
                    "source": "hf_model",
                }

            except Exception as e:
                logger.error(f"HF inference failed: {e}")

        # Fallback: return unknown (to be handled by severity_grader)
        return {
            "severity": None,
            "confidence": 0.0,
            "probabilities": {},
            "source": "fallback",
        }

    def fuse_results(self, model_result: dict, lesion_count: int, lesion_types: dict) -> dict:
        """
        Stabilized hybrid fusion logic.

        Primary source of truth: HF model prediction
        Supporting signal: lesion count + spatial density
        Guard rails prevent contradictory outputs.

        Args:
            model_result: output from classify_global_severity()
            lesion_count: total detected lesions
            lesion_types: dict with counts per type {inflammatory: N, comedonal: N, other: N}

        Returns:
            Fused result dict.
        """
        severity = model_result["severity"]
        confidence = model_result["confidence"]
        source = model_result["source"]

        # If model failed, use rule-based from count
        if severity is None or source == "fallback":
            severity = self._rule_based_severity(lesion_count)
            confidence = 0.6  # lower confidence for rule-based
            source = "rule_based"
        else:
            # Apply guard rails
            original_severity = severity

            # Guard: Model says Severe but very few lesions
            if severity == "Severe" and lesion_count <= 2:
                severity = "Moderate"
                logger.info(f"Fusion guard: {original_severity} → {severity} (only {lesion_count} lesions)")

            # Guard: Model says Clear but many lesions detected
            elif severity == "Clear" and lesion_count >= 15:
                severity = "Mild"
                logger.info(f"Fusion guard: {original_severity} → {severity} ({lesion_count} lesions)")

            # Guard: Model says Clear but moderate lesion count
            elif severity == "Clear" and lesion_count >= 6:
                severity = "Mild"
                logger.info(f"Fusion guard: {original_severity} → {severity} ({lesion_count} lesions)")

            # Guard: Model says Mild but high inflammatory count
            elif severity == "Mild" and lesion_types.get("inflammatory", 0) >= 10:
                severity = "Moderate"
                logger.info(f"Fusion guard: {original_severity} → {severity} (high inflammatory)")

            if severity != original_severity:
                source = "hybrid_fusion"

        # Compute acne coverage estimate from lesion density
        acne_coverage = self._estimate_coverage(lesion_count, lesion_types)

        return {
            "severity": severity,
            "confidence": round(confidence, 4),
            "lesion_count": lesion_count,
            "lesion_types": lesion_types,
            "acne_coverage_pct": acne_coverage,
            "source": source,
        }

    @staticmethod
    def _rule_based_severity(lesion_count: int) -> str:
        """Fallback: rule-based severity from lesion count."""
        if lesion_count <= 2:
            return "Clear"
        elif lesion_count <= 5:
            return "Mild"
        elif lesion_count <= 15:
            return "Moderate"
        else:
            return "Severe"

    @staticmethod
    def _estimate_coverage(lesion_count: int, lesion_types: dict) -> float:
        """Estimate acne coverage percentage from lesion data."""
        # Rough estimate: each lesion covers ~0.3-0.8% of face area
        inflammatory = lesion_types.get("inflammatory", 0)
        comedonal = lesion_types.get("comedonal", 0)
        other = lesion_types.get("other", 0)

        # Inflammatory lesions are typically larger
        coverage = (inflammatory * 0.8) + (comedonal * 0.4) + (other * 0.5)
        return round(min(coverage, 60.0), 1)  # Cap at 60%


# Module-level access
def get_hybrid_analyzer() -> HybridSkinAnalyzer:
    return HybridSkinAnalyzer()


def get_hybrid_model() -> HybridSkinAnalyzer:
    """Backward-compatible alias for startup warm-up imports."""
    return get_hybrid_analyzer()
