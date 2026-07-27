"""Print Readiness Engine - evaluates if artwork is ready for any print method and provides fixes."""

from typing import Optional


# Print methods with their requirements
PRINT_METHODS = {
    "dtf": {
        "name": "DTF (Direct to Film)",
        "min_dpi": 200,
        "ideal_dpi": 300,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": None,
        "min_width_px": 500,
        "min_height_px": 500,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Best all-around transfer method. Requires transparent background.",
    },
    "dtg": {
        "name": "DTG (Direct to Garment)",
        "min_dpi": 200,
        "ideal_dpi": 300,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": None,
        "min_width_px": 500,
        "min_height_px": 500,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Print directly on fabric. Requires transparent PNG. White ink base for darks.",
    },
    "screen_print": {
        "name": "Screen Printing",
        "min_dpi": 150,
        "ideal_dpi": 300,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": 8,
        "min_width_px": 300,
        "min_height_px": 300,
        "supports_gradients": False,
        "supports_fine_detail": False,
        "supports_photo": False,
        "notes": "Spot colors, limited color count. Not suitable for photos or gradients.",
    },
    "sublimation": {
        "name": "Sublimation",
        "min_dpi": 200,
        "ideal_dpi": 300,
        "requires_transparency": False,
        "requires_cmyk": False,
        "max_colors": None,
        "min_width_px": 500,
        "min_height_px": 500,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Full color on polyester/white surfaces. No white ink—background prints as white.",
    },
    "vinyl_cut": {
        "name": "Vinyl Cut (HTV)",
        "min_dpi": 72,
        "ideal_dpi": 150,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": 3,
        "min_width_px": 200,
        "min_height_px": 200,
        "supports_gradients": False,
        "supports_fine_detail": False,
        "supports_photo": False,
        "notes": "Single/few color flat designs only. Must be vector-ready or simple shapes.",
    },
    "embroidery": {
        "name": "Embroidery",
        "min_dpi": 72,
        "ideal_dpi": 150,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": 12,
        "min_width_px": 200,
        "min_height_px": 200,
        "supports_gradients": False,
        "supports_fine_detail": False,
        "supports_photo": False,
        "notes": "Thread-based. No gradients, no fine detail, limited colors. Needs digitizing.",
    },
    "uv_print": {
        "name": "UV Printing",
        "min_dpi": 300,
        "ideal_dpi": 600,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": None,
        "min_width_px": 500,
        "min_height_px": 500,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Hard surfaces (phone cases, wood, metal). Very high DPI needed.",
    },
    "large_format": {
        "name": "Large Format (Poster/Banner)",
        "min_dpi": 72,
        "ideal_dpi": 150,
        "requires_transparency": False,
        "requires_cmyk": True,
        "max_colors": None,
        "min_width_px": 1000,
        "min_height_px": 1000,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Viewed from distance. Lower DPI acceptable but needs large pixel count.",
    },
    "sticker": {
        "name": "Sticker / Label",
        "min_dpi": 300,
        "ideal_dpi": 600,
        "requires_transparency": True,
        "requires_cmyk": False,
        "max_colors": None,
        "min_width_px": 300,
        "min_height_px": 300,
        "supports_gradients": True,
        "supports_fine_detail": True,
        "supports_photo": True,
        "notes": "Contour cut around design. Needs clean edges and transparent background.",
    },
}


class PrintReadinessEngine:
    """Evaluates artwork readiness for all print methods and provides actionable fixes."""

    def analyze(self, width: int, height: int, dpi: int, has_alpha: bool,
                color_space: str, color_complexity: str, has_gradients: bool,
                artwork_type: str, image_quality_score: int) -> dict:
        """Evaluate print readiness across all methods."""

        results = {}
        for method_id, method in PRINT_METHODS.items():
            result = self._evaluate_method(
                method_id, method, width, height, dpi, has_alpha,
                color_space, color_complexity, has_gradients, artwork_type, image_quality_score
            )
            results[method_id] = result

        # Overall readiness
        ready_count = sum(1 for r in results.values() if r["ready"])
        partial_count = sum(1 for r in results.values() if r["status"] == "needs_work")
        total = len(results)

        # Best method recommendation
        best = max(results.values(), key=lambda r: r["score"])

        return {
            "print_methods": results,
            "summary": {
                "ready_count": ready_count,
                "needs_work_count": partial_count,
                "not_suitable_count": total - ready_count - partial_count,
                "total_methods": total,
                "best_method": best["method_name"],
                "best_score": best["score"],
                "overall_ready": ready_count > 0,
            },
        }

    def _evaluate_method(self, method_id: str, method: dict, width: int, height: int,
                          dpi: int, has_alpha: bool, color_space: str,
                          color_complexity: str, has_gradients: bool,
                          artwork_type: str, quality_score: int) -> dict:
        """Evaluate a single print method."""
        score = 100
        issues = []
        fixes = []
        warnings = []

        # DPI check
        if dpi >= method["ideal_dpi"]:
            pass  # Perfect
        elif dpi >= method["min_dpi"]:
            score -= 10
            warnings.append(f"DPI ({dpi}) meets minimum but below ideal ({method['ideal_dpi']})")
            fixes.append(f"Upscale to {method['ideal_dpi']} DPI for best quality")
        else:
            score -= 30
            issues.append(f"DPI ({dpi}) below minimum ({method['min_dpi']})")
            fixes.append(f"AI upscale required. Target: {method['ideal_dpi']} DPI minimum")

        # Transparency
        if method["requires_transparency"] and not has_alpha:
            score -= 25
            issues.append("No transparent background")
            fixes.append("Remove background (AI background removal)")

        # Resolution
        if width < method["min_width_px"] or height < method["min_height_px"]:
            score -= 20
            issues.append(f"Dimensions too small ({width}×{height}px)")
            fixes.append(f"Upscale to at least {method['min_width_px']}×{method['min_height_px']}px")

        # Color count
        if method["max_colors"]:
            if color_complexity == "high":
                score -= 30
                issues.append(f"Too many colors for {method['name']} (max {method['max_colors']})")
                fixes.append(f"Reduce to {method['max_colors']} colors or choose DTF/DTG instead")
            elif color_complexity == "medium":
                score -= 10
                warnings.append(f"Medium color complexity—may exceed {method['max_colors']} color limit")

        # Gradient support
        if has_gradients and not method["supports_gradients"]:
            score -= 20
            issues.append(f"{method['name']} does not support gradients")
            fixes.append("Flatten gradients to solid colors or choose DTF/DTG/sublimation")

        # Photo support
        if artwork_type == "photo" and not method["supports_photo"]:
            score -= 25
            issues.append(f"{method['name']} not suitable for photographic images")
            fixes.append("Use DTF, DTG, or sublimation for photos")

        # Fine detail
        if quality_score < 60 and method["supports_fine_detail"]:
            score -= 10
            warnings.append("Image quality may affect fine detail reproduction")
            fixes.append("Apply AI enhancement to improve detail clarity")

        # CMYK
        if method["requires_cmyk"] and color_space != "CMYK":
            score -= 5
            warnings.append("CMYK color profile recommended")
            fixes.append("Convert to CMYK color profile before printing")

        score = max(0, min(100, score))

        # Status
        if score >= 80:
            status = "ready"
            ready = True
        elif score >= 50:
            status = "needs_work"
            ready = False
        else:
            status = "not_suitable"
            ready = False

        return {
            "method_id": method_id,
            "method_name": method["name"],
            "score": score,
            "status": status,
            "ready": ready,
            "issues": issues,
            "warnings": warnings,
            "fixes": fixes,
            "notes": method["notes"],
            "requirements": {
                "min_dpi": method["min_dpi"],
                "ideal_dpi": method["ideal_dpi"],
                "transparency": method["requires_transparency"],
                "max_colors": method["max_colors"],
                "supports_gradients": method["supports_gradients"],
                "supports_photo": method["supports_photo"],
            },
        }
