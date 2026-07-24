"""Product Intelligence Engine - evaluates product compatibility."""


class ProductIntelligence:
    """Analyzes artwork suitability for various product types."""

    PRODUCTS = [
        {"id": "dtf", "name": "DTF Transfer", "min_dpi": 150, "ideal_dpi": 300, "needs_alpha": True, "max_colors": None},
        {"id": "tshirt", "name": "T-Shirt Printing", "min_dpi": 150, "ideal_dpi": 300, "needs_alpha": True, "max_colors": None},
        {"id": "hoodie", "name": "Hoodie", "min_dpi": 150, "ideal_dpi": 300, "needs_alpha": True, "max_colors": None},
        {"id": "sticker", "name": "Sticker", "min_dpi": 300, "ideal_dpi": 600, "needs_alpha": True, "max_colors": None},
        {"id": "poster", "name": "Poster", "min_dpi": 150, "ideal_dpi": 300, "needs_alpha": False, "max_colors": None},
        {"id": "mug", "name": "Mug", "min_dpi": 200, "ideal_dpi": 300, "needs_alpha": False, "max_colors": None},
        {"id": "cap", "name": "Cap", "min_dpi": 150, "ideal_dpi": 300, "needs_alpha": True, "max_colors": 8},
        {"id": "embroidery", "name": "Embroidery", "min_dpi": 72, "ideal_dpi": 150, "needs_alpha": True, "max_colors": 12},
        {"id": "uv_print", "name": "UV Print", "min_dpi": 300, "ideal_dpi": 600, "needs_alpha": True, "max_colors": None},
        {"id": "sublimation", "name": "Sublimation", "min_dpi": 200, "ideal_dpi": 300, "needs_alpha": False, "max_colors": None},
    ]

    def analyze(self, width: int, height: int, dpi: int, has_alpha: bool,
                color_complexity: str, artwork_type: str, production_score: int) -> dict:
        """Evaluate product compatibility for all product types."""
        results = {}

        for product in self.PRODUCTS:
            compatibility = self._evaluate_product(
                product, width, height, dpi, has_alpha,
                color_complexity, artwork_type, production_score
            )
            results[product["id"]] = compatibility

        return results

    def _evaluate_product(self, product: dict, width: int, height: int,
                           dpi: int, has_alpha: bool, color_complexity: str,
                           artwork_type: str, production_score: int) -> dict:
        """Evaluate a single product compatibility."""
        score = 0
        reasons = []
        issues = []

        # DPI check
        if dpi >= product["ideal_dpi"]:
            score += 40
            reasons.append(f"Resolution exceeds ideal ({product['ideal_dpi']} DPI)")
        elif dpi >= product["min_dpi"]:
            score += 25
            reasons.append(f"Resolution meets minimum ({product['min_dpi']} DPI)")
        else:
            score += 5
            issues.append(f"Resolution below minimum ({dpi} < {product['min_dpi']} DPI)")

        # Alpha channel
        if product["needs_alpha"]:
            if has_alpha:
                score += 30
                reasons.append("Has transparency (required)")
            else:
                score += 10
                issues.append("No transparency - background removal needed")
        else:
            score += 30  # No alpha requirement

        # Color complexity for limited-color products
        if product["max_colors"]:
            if color_complexity == "low":
                score += 20
                reasons.append(f"Low color count suits {product['name']}")
            elif color_complexity == "medium":
                score += 10
                issues.append("Medium color complexity - may need simplification")
            else:
                score += 0
                issues.append(f"High color complexity - exceeds {product['max_colors']} color limit")
        else:
            score += 20

        # Production score influence
        if production_score >= 80:
            score += 10
        elif production_score >= 60:
            score += 5

        # Determine status
        if score >= 80:
            status = "recommended"
        elif score >= 50:
            status = "compatible"
        else:
            status = "not_recommended"

        return {
            "product": product["name"],
            "status": status,
            "score": min(100, score),
            "reasons": reasons,
            "issues": issues,
        }
