"""Generation Plan Builder - produces the final structured JSON for Module 4."""

from datetime import datetime, timezone


class PlanBuilder:
    """Builds the final Generation Plan consumed by Module 4."""

    def build(self, analysis_id: str, artwork_id: str, artwork_ext: str,
              file_inspection: dict, visual: dict, geometry: dict,
              production: dict, products: dict, risks: dict, decisions: dict) -> dict:
        """Build the complete Generation Plan JSON."""

        # Determine recommended model based on decisions
        needs_reconstruction = decisions.get("needs_reconstruction", {}).get("value", False)
        needs_super_res = decisions.get("needs_super_resolution", {}).get("value", False)
        needs_bg_removal = decisions.get("needs_background_removal", {}).get("value", False)

        if needs_reconstruction:
            recommended_model = "GPT Image (Reconstruction)"
        elif needs_super_res:
            recommended_model = "Super Resolution + GPT Image"
        elif needs_bg_removal:
            recommended_model = "Background Removal + Enhancement"
        else:
            recommended_model = "Direct Production"

        # Best product recommendation
        best_product = "DTF"
        best_product_score = 0
        for pid, pdata in products.items():
            if pdata.get("score", 0) > best_product_score and pdata.get("status") == "recommended":
                best_product = pdata.get("product", pid)
                best_product_score = pdata["score"]

        # Overall score
        production_score = production.get("production_score", 50)
        risk_penalty = risks.get("critical_count", 0) * 20 + risks.get("high_count", 0) * 10 + risks.get("medium_count", 0) * 5
        overall_score = max(0, min(100, production_score - risk_penalty))

        plan = {
            "analysis_id": analysis_id,
            "artwork_id": artwork_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",

            # Model recommendation
            "recommended_model": recommended_model,

            # Required operations
            "needs_reconstruction": decisions.get("needs_reconstruction", {}).get("value", False),
            "needs_background_removal": decisions.get("needs_background_removal", {}).get("value", False),
            "needs_super_resolution": decisions.get("needs_super_resolution", {}).get("value", False),
            "needs_vectorization": decisions.get("needs_vectorization", {}).get("value", False),
            "needs_canvas_expansion": decisions.get("needs_canvas_expansion", {}).get("value", False),
            "needs_edge_refinement": decisions.get("needs_edge_refinement", {}).get("value", False),
            "needs_color_cleanup": decisions.get("needs_color_cleanup", {}).get("value", False),
            "needs_noise_reduction": decisions.get("needs_noise_reduction", {}).get("value", False),
            "needs_shadow_removal": decisions.get("needs_shadow_removal", {}).get("value", False),
            "needs_halo_removal": decisions.get("needs_halo_removal", {}).get("value", False),

            # Preservation flags
            "preserve_typography": decisions.get("preserve_typography", {}).get("value", True),
            "preserve_colors": decisions.get("preserve_colors", {}).get("value", True),
            "preserve_composition": decisions.get("preserve_composition", {}).get("value", True),
            "preserve_subject": decisions.get("preserve_subject", {}).get("value", True),
            "preserve_transparency": decisions.get("preserve_transparency", {}).get("value", False),

            # Production parameters
            "recommended_print_width": production.get("safe_print_width_inches", 0),
            "recommended_print_height": production.get("safe_print_height_inches", 0),
            "max_print_width": production.get("max_print_width_inches", 0),
            "max_print_height": production.get("max_print_height_inches", 0),
            "target_dpi": production.get("recommended_dpi", 300),

            # Product
            "recommended_product": best_product,
            "product_compatibility_count": sum(1 for p in products.values() if p.get("status") in ("recommended", "compatible")),

            # Scores
            "risk_level": risks.get("risk_level", "unknown"),
            "risk_count": risks.get("risk_count", 0),
            "production_score": production_score,
            "overall_score": overall_score,

            # Artwork classification
            "artwork_type": visual.get("artwork_type", "unknown"),
            "artistic_style": visual.get("artistic_style", "unknown"),
            "background_type": visual.get("background", {}).get("type", "unknown"),

            # Confidence scores
            "confidence": {
                k: v.get("confidence", 0)
                for k, v in decisions.items()
                if isinstance(v, dict) and "confidence" in v
            },
        }

        return plan
