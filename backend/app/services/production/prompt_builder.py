"""Prompt Builder - converts Generation Plan JSON into model-specific prompts."""


class PromptBuilder:
    """Builds optimized prompts from Generation Plans. Never exposes prompts to users."""

    # Template fragments for different operations
    OPERATION_TEMPLATES = {
        "reconstruction": "Reconstruct and rebuild this artwork while preserving the exact subject, composition, and style. Maintain all visual elements faithfully.",
        "enhancement": "Enhance this artwork for professional DTF printing production. Improve quality while maintaining exact visual fidelity.",
        "upscaling": "Upscale this artwork to high resolution suitable for large format DTF printing at 300 DPI. Preserve all fine details, edges, and textures exactly.",
        "background_cleanup": "Remove the background and produce a clean transparent PNG. Preserve every detail of the subject with clean, smooth edges. No halos or fringing.",
        "edge_refinement": "Refine and smooth all edges of this artwork. Remove any jagged edges, halos, or fringing artifacts. Produce clean anti-aliased boundaries.",
        "production_cleanup": "Clean this artwork for production printing. Remove noise, artifacts, and imperfections while preserving the original design intent exactly.",
    }

    PRESERVE_TEMPLATES = {
        "preserve_typography": "Preserve all text, lettering, and typography exactly as in the original - same fonts, sizes, positions, and styling.",
        "preserve_colors": "Maintain the exact color palette and tones from the original artwork.",
        "preserve_composition": "Keep the exact same layout, positioning, and composition as the original.",
        "preserve_subject": "The primary subject must remain identical to the original in every detail.",
        "preserve_transparency": "Maintain transparent background. Output must be PNG with clean alpha channel.",
    }

    STYLE_CONTEXT = {
        "logo": "This is a logo/brand mark - precision and clean lines are critical.",
        "illustration": "This is an illustration - maintain artistic style and line quality.",
        "photo": "This is a photographic image - maintain photorealistic quality.",
        "cartoon": "This is a cartoon/character artwork - maintain style consistency.",
        "text_design": "This is a text-based design - typography accuracy is paramount.",
        "sticker": "This is a sticker design - clean edges and transparency are essential.",
        "vector": "This is a vector-style artwork - maintain crisp edges and flat colors.",
    }

    def build_prompt(self, generation_plan: dict, mode: str = "enhancement",
                     operations: dict = None, custom_instructions: str = "",
                     target_ratio: str = "", visual_analysis: dict = None) -> str:
        """Build a complete prompt from a generation plan, user settings, and GPT analysis."""
        parts = []

        # 0. Product description from GPT analysis (tells AI exactly what the design is)
        va = visual_analysis or {}
        if va.get("product_description"):
            parts.append(f"This artwork is: {va['product_description']}")

        # 0b. Detailed subject info from GPT
        if va.get("subjects"):
            subject_labels = [s.get("label", "") for s in va["subjects"] if s.get("label")]
            if subject_labels:
                parts.append(f"Main elements: {', '.join(subject_labels)}.")

        # 0c. Style context from GPT
        if va.get("artistic_style") and va["artistic_style"] != "unknown":
            parts.append(f"Artistic style: {va['artistic_style']}.")

        # 0d. Text preservation with actual detected text
        if va.get("typography", {}).get("detected_text"):
            parts.append(f"Contains text that must be preserved exactly: \"{va['typography']['detected_text']}\"")

        # 0e. Color info from GPT
        if va.get("color_analysis", {}).get("dominant_colors"):
            colors = va["color_analysis"]["dominant_colors"]
            if colors and isinstance(colors[0], str):
                parts.append(f"Key colors to maintain: {', '.join(colors[:5])}.")

        # 1. Main operation instruction
        operation_text = self.OPERATION_TEMPLATES.get(mode, self.OPERATION_TEMPLATES["enhancement"])
        parts.append(operation_text)

        # 2. Additional operations requested by user
        ops = operations or {}
        if ops.get("background_removal") and mode != "background_cleanup":
            parts.append("Remove the background completely to produce transparent PNG.")
        if ops.get("super_resolution") and mode != "upscaling":
            parts.append("Maximize resolution and detail clarity for large-format printing.")
        if ops.get("edge_refinement") and mode != "edge_refinement":
            parts.append("Smooth and refine all edges - remove jaggedness and aliasing.")
        if ops.get("noise_reduction"):
            parts.append("Remove all noise, grain, and compression artifacts.")
        if ops.get("color_cleanup"):
            parts.append("Clean and normalize colors for accurate print reproduction.")
        if ops.get("halo_removal"):
            parts.append("Remove any white or bright halos around the subject edges.")
        if ops.get("shadow_removal"):
            parts.append("Remove drop shadows and cast shadows from the subject.")
        if ops.get("canvas_expansion"):
            parts.append("Extend the canvas around the subject to add safe margins for printing.")

        # 3. Artwork type context
        artwork_type = generation_plan.get("artwork_type", "unknown")
        if artwork_type in self.STYLE_CONTEXT:
            parts.append(self.STYLE_CONTEXT[artwork_type])

        # 4. Preservation requirements
        for key, template in self.PRESERVE_TEMPLATES.items():
            if generation_plan.get(key, False):
                parts.append(template)

        # 5. Target aspect ratio
        if target_ratio:
            parts.append(f"Output should match aspect ratio {target_ratio} for DTF printing.")

        # 6. Production requirements
        target_dpi = generation_plan.get("target_dpi", 300)
        parts.append(f"Output must be suitable for {target_dpi} DPI professional DTF printing.")

        # 7. Background handling
        if generation_plan.get("needs_background_removal") or ops.get("background_removal"):
            parts.append("Final output must have fully transparent background (PNG with alpha).")
        elif generation_plan.get("background_type") == "transparent":
            parts.append("Maintain the transparent background.")

        # 8. Quality requirements
        parts.append("Output must be the highest possible quality with no artifacts, noise, or compression damage.")
        parts.append("Do not add any watermarks, text, borders, or elements not in the original.")

        # 9. Custom instructions from user
        if custom_instructions.strip():
            parts.append(f"Additional requirement: {custom_instructions.strip()}")

        return " ".join(parts)

    def build_negative_prompt(self, generation_plan: dict) -> str:
        """Build a negative prompt (for models that support it)."""
        negatives = [
            "blurry", "low quality", "pixelated", "artifacts", "noise",
            "watermark", "text overlay", "border", "frame",
            "distorted", "deformed", "extra elements",
        ]

        if generation_plan.get("preserve_typography"):
            negatives.extend(["wrong text", "misspelled", "different font"])

        if generation_plan.get("background_type") == "transparent":
            negatives.extend(["white background", "colored background"])

        return ", ".join(negatives)
