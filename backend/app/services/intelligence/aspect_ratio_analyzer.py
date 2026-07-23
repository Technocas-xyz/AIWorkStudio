"""Aspect Ratio Intelligence - analyzes current ratio and recommends target ratios with risk."""

import math
from typing import Optional
from app.services.aspect_ratio_service import calculate_aspect_ratio, get_orientation


# Common DTF production target aspect ratios (max print area: 20" x 28")
TARGET_RATIOS = [
    {"name": "1:1", "ratio": 1.0, "use_cases": ["Square chest print", "Back center", "Pocket print", "Badge"]},
    {"name": "1:2", "ratio": 0.5, "use_cases": ["Tall narrow", "Bookmark", "Sleeve", "Leg print"]},
    {"name": "2:1", "ratio": 2.0, "use_cases": ["Wide banner", "Waistband", "Cap wrap"]},
    {"name": "2:3", "ratio": 0.667, "use_cases": ["Tall print", "Sleeve", "Phone case"]},
    {"name": "3:2", "ratio": 1.5, "use_cases": ["Wide landscape", "Back yoke", "Lower back"]},
    {"name": "3:4", "ratio": 0.75, "use_cases": ["Standard front", "Large back", "Tote bag"]},
    {"name": "4:3", "ratio": 1.333, "use_cases": ["Landscape chest", "Cap front", "Wide design"]},
    {"name": "4:5", "ratio": 0.8, "use_cases": ["Portrait DTF", "Standard tall", "Hoodie back"]},
    {"name": "5:4", "ratio": 1.25, "use_cases": ["Wide chest", "Landscape print"]},
    {"name": "5:7", "ratio": 0.714, "use_cases": ["Most common DTF", "Standard t-shirt front", "Back print"]},
    {"name": "7:5", "ratio": 1.4, "use_cases": ["Wide landscape", "Banner chest"]},
    {"name": "9:16", "ratio": 0.5625, "use_cases": ["Very tall", "Full leg", "Story format"]},
    {"name": "16:9", "ratio": 1.778, "use_cases": ["Extra wide", "Across back", "Hem print"]},
    {"name": "10:13", "ratio": 0.769, "use_cases": ["Standard chest", "Popular DTF size"]},
    {"name": "11:14", "ratio": 0.786, "use_cases": ["Wide front", "Hoodie front"]},
]

# Maximum DTF print area
MAX_PRINT_WIDTH = 20  # inches
MAX_PRINT_HEIGHT = 28  # inches


class AspectRatioAnalyzer:
    """Analyzes aspect ratio compatibility and recommends target ratios with risk assessment."""

    def analyze(self, width: int, height: int, has_alpha: bool,
                subject_coverage_pct: float, edge_contact: dict,
                bounding_box: dict) -> dict:
        """Analyze current aspect ratio and evaluate all DTF target ratios."""
        if width == 0 or height == 0:
            return {"error": "Invalid dimensions", "current_ratio": 0, "recommendations": []}

        current_ratio = width / height
        current_ratio_str = self._ratio_to_string(width, height)

        # Full aspect ratio info from centralized service
        ar_info = calculate_aspect_ratio(width, height)

        # Calculate current max print size at 300 DPI
        max_print_w_300 = round(width / 300, 2)
        max_print_h_300 = round(height / 300, 2)

        # Clamp to max DTF area
        actual_max_w = min(max_print_w_300, MAX_PRINT_WIDTH)
        actual_max_h = min(max_print_h_300, MAX_PRINT_HEIGHT)

        recommendations = []
        for target in TARGET_RATIOS:
            rec = self._evaluate_target(
                current_ratio, target["ratio"], target["name"], target["use_cases"],
                width, height, has_alpha, subject_coverage_pct, edge_contact, bounding_box
            )
            recommendations.append(rec)

        # Sort by compatibility score (best first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        # Determine best match
        best = recommendations[0] if recommendations else None

        return {
            "current_ratio": round(current_ratio, 4),
            "current_ratio_display": ar_info["aspect_ratio"],
            "current_orientation": ar_info["orientation"],
            "current_category": ar_info["category"],
            "max_dtf_area": f"{MAX_PRINT_WIDTH}\" × {MAX_PRINT_HEIGHT}\"",
            "max_print_at_300dpi": f"{max_print_w_300}\" × {max_print_h_300}\"",
            "effective_max_print": f"{actual_max_w}\" × {actual_max_h}\"",
            "best_match": best["name"] if best else None,
            "best_match_score": best["score"] if best else 0,
            "best_print_size": best["max_print_size"] if best else None,
            "recommendations": recommendations,
            "summary": self._generate_summary(current_ratio, recommendations),
        }

    def _evaluate_target(self, current_ratio: float, target_ratio: float,
                          name: str, use_cases: list, width: int, height: int,
                          has_alpha: bool, coverage: float,
                          edge_contact: dict, bbox: dict) -> dict:
        """Evaluate a single target aspect ratio for DTF production."""
        ratio_diff = abs(current_ratio - target_ratio)
        ratio_diff_pct = (ratio_diff / current_ratio) * 100 if current_ratio > 0 else 100

        # Determine transformation needed
        if abs(ratio_diff) < 0.02:
            transform = "none"
            method = "Direct use - no transformation needed"
        elif target_ratio > current_ratio:
            # Target is wider - need to add width or crop height
            transform = "widen"
            method = "Add canvas width (AI expand) or crop top/bottom"
        else:
            # Target is taller - need to add height or crop width
            transform = "heighten"
            method = "Add canvas height (AI expand) or crop left/right"

        # Calculate what cropping would lose
        crop_loss_pct = 0
        if transform == "widen":
            new_height = width / target_ratio
            if new_height < height:
                crop_loss_pct = ((height - new_height) / height) * 100
        elif transform == "heighten":
            new_width = height * target_ratio
            if new_width < width:
                crop_loss_pct = ((width - new_width) / width) * 100

        # Calculate canvas expansion needed
        expand_pct = 0
        if transform == "widen":
            target_width = height * target_ratio
            if target_width > width:
                expand_pct = ((target_width - width) / width) * 100
        elif transform == "heighten":
            target_height = width / target_ratio
            if target_height > height:
                expand_pct = ((target_height - height) / height) * 100

        # DTF print size calculations
        # Calculate the max print size for this ratio within the 20x28 DTF area
        if target_ratio >= 1.0:
            # Landscape or square: width is the limiting factor
            target_print_w = min(MAX_PRINT_WIDTH, MAX_PRINT_HEIGHT * target_ratio)
            target_print_h = target_print_w / target_ratio
        else:
            # Portrait: height is the limiting factor
            target_print_h = min(MAX_PRINT_HEIGHT, MAX_PRINT_WIDTH / target_ratio)
            target_print_w = target_print_h * target_ratio

        target_print_w = round(min(target_print_w, MAX_PRINT_WIDTH), 1)
        target_print_h = round(min(target_print_h, MAX_PRINT_HEIGHT), 1)

        # Calculate required DPI for max print at this ratio
        required_dpi_w = width / target_print_w if target_print_w > 0 else 0
        required_dpi_h = height / target_print_h if target_print_h > 0 else 0
        effective_dpi = round(min(required_dpi_w, required_dpi_h))

        # DPI quality assessment
        if effective_dpi >= 300:
            dpi_quality = "excellent"
        elif effective_dpi >= 200:
            dpi_quality = "good"
        elif effective_dpi >= 150:
            dpi_quality = "low"
        else:
            dpi_quality = "insufficient"

        # Risk assessment
        risks = []
        severity = "low"

        if ratio_diff_pct > 50:
            risks.append("Extreme ratio change - significant distortion or content loss")
            severity = "critical"
        elif ratio_diff_pct > 30:
            risks.append("Major ratio change - notable content restructuring needed")
            severity = "high"
        elif ratio_diff_pct > 15:
            risks.append("Moderate ratio change - some adjustment needed")
            severity = "medium"

        if crop_loss_pct > 30:
            risks.append(f"Cropping would remove {crop_loss_pct:.0f}% of content")
            severity = "high" if severity != "critical" else severity
        elif crop_loss_pct > 15:
            risks.append(f"Cropping would remove {crop_loss_pct:.0f}% of content")
            if severity == "low":
                severity = "medium"

        if expand_pct > 50:
            risks.append(f"Canvas expansion of {expand_pct:.0f}% needs AI generation")
            if severity == "low":
                severity = "medium"

        if effective_dpi < 200:
            risks.append(f"Only {effective_dpi} DPI at {target_print_w}\"×{target_print_h}\" - below minimum 200 DPI for DTF")
            if severity == "low":
                severity = "high" if effective_dpi < 150 else "medium"

        # Edge contact risk
        if transform == "heighten" and (edge_contact.get("left") or edge_contact.get("right")):
            risks.append("Subject touches side edges - cropping will cut into subject")
            severity = "high"
        if transform == "widen" and (edge_contact.get("top") or edge_contact.get("bottom")):
            risks.append("Subject touches top/bottom edges - cropping will cut into subject")
            severity = "high"

        # Score (100 = perfect match, 0 = impossible)
        score = 100
        score -= min(40, ratio_diff_pct * 0.8)
        score -= min(30, crop_loss_pct * 0.6)
        score -= min(20, expand_pct * 0.3)
        if effective_dpi < 200:
            score -= min(20, (200 - effective_dpi) * 0.2)
        if not has_alpha and transform != "none":
            score -= 5
        score = max(0, min(100, score))

        # Determine recommendation status
        if score >= 85:
            status = "recommended"
        elif score >= 60:
            status = "possible"
        elif score >= 35:
            status = "risky"
        else:
            status = "not_recommended"

        return {
            "name": name,
            "target_ratio": target_ratio,
            "max_print_size": f"{target_print_w}\" × {target_print_h}\"",
            "use_cases": use_cases,
            "status": status,
            "score": round(score),
            "severity": severity,
            "transform_needed": transform,
            "method": method,
            "ratio_difference_pct": round(ratio_diff_pct, 1),
            "crop_loss_pct": round(crop_loss_pct, 1),
            "canvas_expand_pct": round(expand_pct, 1),
            "effective_dpi": effective_dpi,
            "dpi_quality": dpi_quality,
            "risks": risks,
            "ai_expansion_needed": expand_pct > 5,
            "can_crop_safely": crop_loss_pct < 20 and severity not in ("high", "critical"),
        }

    def _ratio_to_string(self, width: int, height: int) -> str:
        """Convert dimensions to a simplified ratio string using centralized service."""
        result = calculate_aspect_ratio(width, height)
        return result["aspect_ratio"]

    def _generate_summary(self, current_ratio: float, recommendations: list) -> str:
        """Generate a human-readable summary for DTF production."""
        recommended = [r for r in recommendations if r["status"] == "recommended"]
        possible = [r for r in recommendations if r["status"] == "possible"]

        if len(recommended) >= 5:
            return f"Versatile for DTF - fits {len(recommended)} standard sizes. Max print area: {MAX_PRINT_WIDTH}\"×{MAX_PRINT_HEIGHT}\"."
        elif len(recommended) >= 3:
            names = ", ".join(r["name"] for r in recommended[:3])
            return f"Good DTF flexibility. Best fits: {names}."
        elif len(recommended) >= 1:
            best = recommended[0]
            return f"Best DTF match: {best['name']} at {best['print_size']}. {len(possible)} other sizes possible with adjustment."
        elif len(possible) >= 1:
            return f"No ideal DTF match. {len(possible)} sizes achievable with cropping/expansion."
        else:
            return "Difficult to adapt for standard DTF sizes without significant modification."
