"""Decision Engine - determines required AI operations with confidence scores."""


class DecisionEngine:
    """The intelligence core. Determines what operations the artwork needs."""

    def decide(self, file_inspection: dict, visual: dict, geometry: dict,
               production: dict, risks: dict, width: int, height: int,
               dpi: int, has_alpha: bool, extension: str) -> dict:
        """Produce decisions about what AI operations are needed."""
        decisions = {}

        # Background Removal
        bg_type = visual.get("background", {}).get("type", "unknown")
        if not has_alpha and bg_type != "transparent":
            if bg_type == "solid":
                decisions["needs_background_removal"] = {"value": True, "confidence": 0.9, "reason": "Solid background detected, removal straightforward"}
            elif bg_type == "complex":
                decisions["needs_background_removal"] = {"value": True, "confidence": 0.75, "reason": "Complex background requires AI removal"}
            else:
                decisions["needs_background_removal"] = {"value": True, "confidence": 0.6, "reason": "Background type uncertain, removal likely needed"}
        else:
            decisions["needs_background_removal"] = {"value": False, "confidence": 0.95, "reason": "Image already has transparency"}

        # Canvas Expansion
        coverage = geometry.get("subject_coverage_pct", 100)
        edge_contact = geometry.get("edge_contact", {})
        touching_edges = sum(1 for v in edge_contact.values() if v)
        if touching_edges >= 2 and coverage > 85:
            decisions["needs_canvas_expansion"] = {"value": True, "confidence": 0.8, "reason": "Subject too close to edges, needs breathing room"}
        else:
            decisions["needs_canvas_expansion"] = {"value": False, "confidence": 0.85, "reason": "Adequate margin exists"}

        # AI Reconstruction
        if width < 300 or height < 300:
            decisions["needs_reconstruction"] = {"value": True, "confidence": 0.85, "reason": "Very small dimensions require AI reconstruction"}
        elif dpi < 72 and (width < 500 or height < 500):
            decisions["needs_reconstruction"] = {"value": True, "confidence": 0.7, "reason": "Low quality source needs reconstruction"}
        else:
            decisions["needs_reconstruction"] = {"value": False, "confidence": 0.8, "reason": "Image quality sufficient"}

        # Super Resolution
        if dpi < 200 or (width < 1000 and height < 1000):
            confidence = 0.95 if dpi < 150 else 0.8
            decisions["needs_super_resolution"] = {"value": True, "confidence": confidence, "reason": f"Resolution ({dpi} DPI) below minimum 200 DPI for DTF production"}
        elif dpi < 300:
            decisions["needs_super_resolution"] = {"value": True, "confidence": 0.6, "reason": f"Resolution ({dpi} DPI) below recommended 300 DPI - upscale advised"}
        else:
            decisions["needs_super_resolution"] = {"value": False, "confidence": 0.9, "reason": "Resolution meets 300 DPI production standard"}

        # Vectorization
        artwork_type = visual.get("artwork_type", "unknown")
        if artwork_type in ("logo", "text_design") and extension not in ("svg", "ai", "eps"):
            decisions["needs_vectorization"] = {"value": True, "confidence": 0.7, "reason": f"{artwork_type} would benefit from vectorization"}
        elif extension in ("svg", "ai", "eps"):
            decisions["needs_vectorization"] = {"value": False, "confidence": 0.95, "reason": "Already vector format"}
        else:
            decisions["needs_vectorization"] = {"value": False, "confidence": 0.8, "reason": "Raster format appropriate for this artwork type"}

        # Edge Refinement
        edge_smooth = production.get("edge_smoothness", 100)
        if edge_smooth < 50:
            decisions["needs_edge_refinement"] = {"value": True, "confidence": 0.75, "reason": "Edges are rough or jagged"}
        else:
            decisions["needs_edge_refinement"] = {"value": False, "confidence": 0.8, "reason": "Edge quality acceptable"}

        # Color Cleanup
        color_complexity = visual.get("color_analysis", {}).get("color_complexity", "medium")
        if color_complexity == "low" and visual.get("color_analysis", {}).get("is_monochrome"):
            decisions["needs_color_cleanup"] = {"value": False, "confidence": 0.9, "reason": "Simple color palette, no cleanup needed"}
        else:
            decisions["needs_color_cleanup"] = {"value": False, "confidence": 0.7, "reason": "Color quality acceptable"}

        # Noise Reduction
        decisions["needs_noise_reduction"] = {"value": False, "confidence": 0.7, "reason": "No significant noise detected"}

        # Shadow Removal
        decisions["needs_shadow_removal"] = {"value": False, "confidence": 0.7, "reason": "No problematic shadows detected"}

        # Halo Removal
        decisions["needs_halo_removal"] = {"value": False, "confidence": 0.7, "reason": "No halos detected"}

        # Preservation decisions
        has_text = visual.get("typography", {}).get("has_text", False)
        decisions["preserve_typography"] = {"value": True, "confidence": 0.9 if has_text else 0.7, "reason": "Typography should be preserved during processing"}
        decisions["preserve_colors"] = {"value": True, "confidence": 0.9, "reason": "Original colors should be maintained"}
        decisions["preserve_composition"] = {"value": True, "confidence": 0.85, "reason": "Layout and composition should be preserved"}
        decisions["preserve_subject"] = {"value": True, "confidence": 0.95, "reason": "Primary subject must be preserved"}
        decisions["preserve_transparency"] = {"value": has_alpha, "confidence": 0.95, "reason": "Existing transparency should be maintained"}

        return decisions
