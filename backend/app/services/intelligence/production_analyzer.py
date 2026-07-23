"""Production Analysis Engine - evaluates print readiness and production quality."""

import math
from typing import Optional


class ProductionAnalyzer:
    """Evaluates production readiness, print quality, and sizing."""

    def analyze(self, width: int, height: int, dpi: Optional[int], extension: str,
                color_space: Optional[str], has_alpha: bool, file_size: int,
                geometry: dict, visual: dict) -> dict:
        """Perform production analysis."""
        effective_dpi = dpi or 72
        minimum_dpi = 200
        recommended_dpi = 300

        # Calculate print sizes
        safe_print_width = round(width / recommended_dpi, 2) if width else 0
        safe_print_height = round(height / recommended_dpi, 2) if height else 0

        # Max at minimum acceptable DPI (200)
        max_print_width_200 = round(width / minimum_dpi, 2) if width else 0
        max_print_height_200 = round(height / minimum_dpi, 2) if height else 0

        max_enlarge_factor = min(4.0, recommended_dpi / max(effective_dpi, 1) * 2)
        max_print_width = round(safe_print_width * max_enlarge_factor, 2)
        max_print_height = round(safe_print_height * max_enlarge_factor, 2)

        # Print quality score (0-100)
        quality_score = self._calculate_quality_score(
            width, height, effective_dpi, has_alpha, geometry, visual
        )

        # Edge smoothness (based on resolution)
        edge_smoothness = min(100, int((min(width, height) / 500) * 100)) if width and height else 0

        # Fine detail score
        fine_detail = min(100, int((effective_dpi / 300) * 100))

        # Color complexity
        color_complexity = visual.get("color_analysis", {}).get("color_complexity", "medium")

        # Production difficulty
        difficulty = self._assess_difficulty(
            width, height, effective_dpi, has_alpha, extension, geometry, visual
        )

        return {
            "safe_print_width_inches": safe_print_width,
            "safe_print_height_inches": safe_print_height,
            "max_print_width_inches": max_print_width,
            "max_print_height_inches": max_print_height,
            "max_print_at_200dpi_width": max_print_width_200,
            "max_print_at_200dpi_height": max_print_height_200,
            "min_enlarge_factor": 0.5,
            "max_enlarge_factor": round(max_enlarge_factor, 2),
            "effective_dpi": effective_dpi,
            "minimum_dpi": minimum_dpi,
            "recommended_dpi": recommended_dpi,
            "dpi_status": "excellent" if effective_dpi >= 300 else "good" if effective_dpi >= 200 else "insufficient",
            "print_quality_score": quality_score,
            "transparency_quality": "excellent" if has_alpha else "n/a",
            "edge_smoothness": edge_smoothness,
            "color_complexity": color_complexity,
            "fine_detail_score": fine_detail,
            "small_text_risk": width < 800 or height < 800,
            "production_difficulty": difficulty,
            "production_score": quality_score,
        }

    def _calculate_quality_score(self, width: int, height: int, dpi: int,
                                  has_alpha: bool, geometry: dict, visual: dict) -> int:
        """Calculate overall print quality score 0-100."""
        score = 50  # Base score

        # Resolution contribution (up to +30)
        total_pixels = (width or 0) * (height or 0)
        if total_pixels >= 4000000:  # 4MP+
            score += 30
        elif total_pixels >= 1000000:  # 1MP+
            score += 20
        elif total_pixels >= 250000:
            score += 10
        else:
            score -= 10

        # DPI contribution (up to +15)
        if dpi >= 300:
            score += 15
        elif dpi >= 150:
            score += 10
        elif dpi >= 72:
            score += 5

        # Alpha/transparency quality (+10)
        if has_alpha:
            score += 10

        # Subject coverage (centered, good use of canvas)
        coverage = geometry.get("subject_coverage_pct", 50)
        if 60 <= coverage <= 95:
            score += 5
        elif coverage < 30:
            score -= 5

        # Edge contact penalty
        if geometry.get("cropping_risk"):
            score -= 10

        return max(0, min(100, score))

    def _assess_difficulty(self, width: int, height: int, dpi: int,
                            has_alpha: bool, extension: str,
                            geometry: dict, visual: dict) -> str:
        """Assess production difficulty level."""
        difficulty_score = 0

        if dpi < 150:
            difficulty_score += 2
        if width < 500 or height < 500:
            difficulty_score += 2
        if not has_alpha:
            difficulty_score += 1  # May need background removal
        if geometry.get("cropping_risk"):
            difficulty_score += 1
        if geometry.get("subject_coverage_pct", 100) < 40:
            difficulty_score += 1
        if extension in ("psd", "psb"):
            difficulty_score += 1

        bg_type = visual.get("background", {}).get("type", "solid")
        if bg_type == "complex":
            difficulty_score += 2

        if difficulty_score <= 1:
            return "easy"
        elif difficulty_score <= 3:
            return "moderate"
        elif difficulty_score <= 5:
            return "challenging"
        else:
            return "complex"
