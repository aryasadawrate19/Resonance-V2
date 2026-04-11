"""
AI Routine Generator — Gemini API integration for personalized skincare routines.
Uses the new google.genai SDK (replaces deprecated google.generativeai).
Falls back to static routines if API is unavailable.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RoutineGenerator:
    """Generate personalized skincare routines using Gemini API."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
            cls._instance._loaded = False
        return cls._instance

    def _load_gemini(self):
        """Lazy load Gemini client."""
        if self._loaded:
            return

        self._loaded = True
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.warning("GEMINI_API_KEY not set. Using static fallback routines.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            logger.info("Gemini API (google.genai) configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            self._client = None

    async def generate_routine(self, skin_profile: dict) -> dict:
        """
        Generate a personalized skincare routine.

        Args:
            skin_profile: dict with skin analysis results + lifestyle inputs

        Returns:
            Structured routine with morning/night steps
        """
        self._load_gemini()

        if self._client is not None:
            try:
                return await self._gemini_generate(skin_profile)
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")

        # Fallback
        return self._static_fallback(skin_profile)

    async def _gemini_generate(self, profile: dict) -> dict:
        """Generate routine using Gemini API (new google.genai SDK)."""
        prompt = self._build_prompt(profile)

        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text

        # Try to parse as JSON
        try:
            # Extract JSON from potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())
            result["disclaimer"] = "This is an AI-generated routine for educational purposes only. Not a medical prescription. Consult a dermatologist before starting any new skincare regimen."
            return result

        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse Gemini response as JSON, using fallback")
            return self._parse_text_response(text, profile)

    def _build_prompt(self, profile: dict) -> str:
        """Build structured prompt for Gemini."""
        return f"""You are a dermatology-informed AI skincare advisor. Generate a personalized skincare routine as JSON.

SKIN PROFILE:
- Skin Type: {profile.get('skin_type', 'combination')}
- Acne Severity: {profile.get('acne_severity', 'Mild')}
- Acne Coverage: {profile.get('acne_coverage_pct', 5)}%
- Lesion Count: {profile.get('lesion_count', 3)}
- Hyperpigmentation: {profile.get('hyperpigmentation_pct', 10)}%
- Skin Health Score: {profile.get('skin_health_score', 65)}/100

LIFESTYLE:
- Sleep Quality: {profile.get('sleep_quality', 3)}/5
- Diet Quality: {profile.get('diet_quality', 3)}/5
- Stress Level: {profile.get('stress_level', 3)}/5
- Climate: {profile.get('climate_zone', 'tropical')}

Return ONLY valid JSON in this exact structure:
{{
    "morning_routine": [
        {{
            "step": 1,
            "action": "Cleanse",
            "product_type": "Gentle foaming cleanser",
            "key_ingredient": "Salicylic acid 0.5%",
            "why": "Removes overnight sebum without over-stripping",
            "budget_option": "CeraVe SA Cleanser (~$12)",
            "premium_option": "La Roche-Posay Effaclar (~$25)"
        }}
    ],
    "night_routine": [
        {{
            "step": 1,
            "action": "Double cleanse",
            "product_type": "Oil cleanser + water cleanser",
            "key_ingredient": "Micellar water",
            "why": "Removes sunscreen and daily buildup",
            "budget_option": "Simple Micellar Water (~$8)",
            "premium_option": "DHC Deep Cleansing Oil (~$28)"
        }}
    ],
    "priority_ingredients": ["niacinamide", "salicylic acid", "SPF"],
    "expected_timeline": "Visible improvement in 2-4 weeks with consistent use",
    "climate_note": "Adjust product textures for your climate"
}}

Make the routine specific to the skin profile above. Include 4-6 steps per routine.
For {profile.get('climate_zone', 'tropical')} climate, prefer {'lighter, gel-based textures' if profile.get('climate_zone', '') in ['tropical', 'humid'] else 'richer, cream-based textures'}.
Focus on {'acne-fighting ingredients' if profile.get('acne_severity', '') in ['Moderate', 'Severe'] else 'maintenance and prevention'}.
{'Prioritize pigmentation-reducing ingredients like niacinamide, vitamin C, and arbutin.' if profile.get('hyperpigmentation_pct', 0) > 15 else ''}"""

    def _parse_text_response(self, text: str, profile: dict) -> dict:
        """Parse unstructured text response into routine format."""
        # Return a structured fallback based on the text response
        return {
            "morning_routine": [
                {
                    "step": 1,
                    "action": "Cleanse",
                    "product_type": "Gentle cleanser",
                    "key_ingredient": "Salicylic acid" if profile.get("acne_severity") in ["Moderate", "Severe"] else "Glycerin",
                    "why": "Clean skin surface",
                    "budget_option": "CeraVe Foaming Cleanser",
                    "premium_option": "La Roche-Posay Effaclar",
                },
                {
                    "step": 2,
                    "action": "Treat",
                    "product_type": "Active serum",
                    "key_ingredient": "Niacinamide 10%",
                    "why": "Reduces inflammation and pigmentation",
                    "budget_option": "The Ordinary Niacinamide",
                    "premium_option": "Paula's Choice Niacinamide Booster",
                },
                {
                    "step": 3,
                    "action": "Moisturize",
                    "product_type": "Lightweight moisturizer",
                    "key_ingredient": "Ceramides",
                    "why": "Restore skin barrier",
                    "budget_option": "CeraVe Moisturizing Lotion",
                    "premium_option": "First Aid Beauty Ultra Repair Cream",
                },
                {
                    "step": 4,
                    "action": "Protect",
                    "product_type": "Sunscreen SPF 50",
                    "key_ingredient": "Zinc oxide / chemical filters",
                    "why": "Prevent UV damage and pigmentation",
                    "budget_option": "Neutrogena Ultra Sheer SPF 50",
                    "premium_option": "EltaMD UV Clear SPF 46",
                },
            ],
            "night_routine": [
                {
                    "step": 1,
                    "action": "Cleanse",
                    "product_type": "Oil / micellar cleanser",
                    "key_ingredient": "Micellar water",
                    "why": "Remove makeup and sunscreen",
                    "budget_option": "Garnier Micellar Water",
                    "premium_option": "Bioderma Sensibio",
                },
                {
                    "step": 2,
                    "action": "Exfoliate (2-3x/week)",
                    "product_type": "Chemical exfoliant",
                    "key_ingredient": "AHA/BHA",
                    "why": "Accelerate cell turnover",
                    "budget_option": "The Ordinary AHA 30%",
                    "premium_option": "Drunk Elephant T.L.C. Sukari",
                },
                {
                    "step": 3,
                    "action": "Treat",
                    "product_type": "Retinoid",
                    "key_ingredient": "Retinol 0.3-0.5%",
                    "why": "Boost collagen and reduce acne",
                    "budget_option": "The Ordinary Retinol 0.5%",
                    "premium_option": "Skinceuticals Retinol 0.5",
                },
                {
                    "step": 4,
                    "action": "Moisturize",
                    "product_type": "Night cream",
                    "key_ingredient": "Ceramides + peptides",
                    "why": "Overnight repair and hydration",
                    "budget_option": "CeraVe PM Moisturizer",
                    "premium_option": "Dr. Jart Ceramidin Cream",
                },
            ],
            "priority_ingredients": self._get_priority_ingredients(profile),
            "expected_timeline": "Visible improvement in 2-4 weeks with consistent use",
            "climate_note": self._get_climate_note(profile.get("climate_zone", "tropical")),
            "disclaimer": "This is an AI-generated routine for educational purposes only. Not a medical prescription.",
        }

    def _static_fallback(self, profile: dict) -> dict:
        """Static fallback routine when Gemini is unavailable."""
        return self._parse_text_response("", profile)

    @staticmethod
    def _get_priority_ingredients(profile: dict) -> list:
        """Determine priority ingredients based on skin profile."""
        ingredients = []

        severity = profile.get("acne_severity", "Mild")
        if severity in ["Moderate", "Severe"]:
            ingredients.extend(["salicylic acid", "benzoyl peroxide", "retinoid"])
        elif severity == "Mild":
            ingredients.extend(["niacinamide", "salicylic acid"])

        if profile.get("hyperpigmentation_pct", 0) > 10:
            ingredients.extend(["vitamin C", "arbutin", "niacinamide"])

        ingredients.append("SPF 50")

        # Deduplicate
        return list(dict.fromkeys(ingredients))

    @staticmethod
    def _get_climate_note(climate: str) -> str:
        """Generate climate-specific note."""
        notes = {
            "tropical": "Use lightweight, gel-based products. Double down on SPF due to high UV exposure.",
            "humid": "Opt for oil-free, water-based formulations. Consider mattifying products.",
            "arid": "Focus on hydration with heavier creams and hyaluronic acid.",
            "temperate": "Standard textures work well. Adjust seasonally.",
            "cold": "Use richer creams to combat dryness. Add facial oils in winter.",
        }
        return notes.get(climate, notes["temperate"])


# Module-level access
_generator = None

def get_routine_generator() -> RoutineGenerator:
    global _generator
    if _generator is None:
        _generator = RoutineGenerator()
    return _generator
