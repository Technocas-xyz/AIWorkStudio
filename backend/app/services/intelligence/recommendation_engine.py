"""Recommendation Engine - generates actionable steps to make artwork production-perfect."""

from typing import Optional


class RecommendationEngine:
    """Generates prioritized, actionable recommendations to improve artwork for DTF production."""

    def recommend(self, file_inspection: dict, visual: dict, geometry: dict,
                  production: dict, risks: dict, decisions: dict,
                  aspect_ratio: dict, width: int, height: int,
                  dpi: int, has_alpha: bool, extension: str) -> dict:
        """Generate comprehensive improvement recommendations."""
        actions = []
        priority_order = 0

        # 1. Resolution / DPI Improvement
        if dpi < 300:
            priority_order += 1
            target_w = width * (300 / max(dpi, 1))
            target_h = height * (300 / max(dpi, 1))
            is_critical = dpi < 200
            actions.append({
                "priority": priority_order,
                "category": "resolution",
                "title": "Increase Resolution to 300 DPI" if dpi < 200 else "Optimize to 300 DPI",
                "severity": "high" if is_critical else "medium",
                "current": f"{width}Ã—{height}px at {dpi} DPI",
                "recommended": f"{int(target_w)}Ã—{int(target_h)}px at 300 DPI",
                "method": "AI Super Resolution (4x upscale)" if is_critical else "AI Super Resolution (2x upscale)",
                "impact": "Below minimum 200 DPI - will pixelate when printed" if is_critical else "Currently at {dpi} DPI - 300 DPI recommended for sharpest output",
                "steps": [
                    f"Current: {dpi} DPI ({'BELOW MINIMUM 200 DPI' if is_critical else 'below recommended 300 DPI'})",
                    f"Minimum for DTF: 200 DPI | Recommended: 300 DPI",
                    f"Apply AI super-resolution to upscale from {width}Ã—{height} to {int(target_w)}Ã—{int(target_h)}",
                    f"After upscale, max print @300dpi: {target_w/300:.1f}\" Ã— {target_h/300:.1f}\"",
                    f"Max print @200dpi: {target_w/200:.1f}\" Ã— {target_h/200:.1f}\"",
                ],
                "auto_fixable": True,
            })

        # 2. Background Removal
        if decisions.get("needs_background_removal", {}).get("value"):
            priority_order += 1
            bg_type = visual.get("background", {}).get("type", "unknown")
            confidence = decisions["needs_background_removal"].get("confidence", 0)
            actions.append({
                "priority": priority_order,
                "category": "background",
                "title": "Remove Background",
                "severity": "high" if bg_type == "complex" else "medium",
                "current": f"{bg_type.capitalize()} background, no transparency",
                "recommended": "Transparent PNG with clean edges",
                "method": "AI Background Removal" if bg_type == "complex" else "Color-key removal",
                "impact": "Required for DTF printing - garment color shows through transparent areas",
                "steps": [
                    f"Detected {bg_type} background ({confidence:.0%} confidence)",
                    "Apply AI background removal to isolate subject",
                    "Review edges for artifacts or halos",
                    "Export as PNG with alpha channel",
                    "Verify no stray pixels remain in transparent areas",
                ],
                "auto_fixable": True,
            })

        # 3. Canvas / Aspect Ratio Adjustment
        best_ratio = aspect_ratio.get("best_match") if aspect_ratio else None
        best_score = aspect_ratio.get("best_match_score", 100) if aspect_ratio else 100
        if best_score < 85 and aspect_ratio:
            priority_order += 1
            recs = aspect_ratio.get("recommendations", [])
            top_rec = recs[0] if recs else None
            actions.append({
                "priority": priority_order,
                "category": "canvas",
                "title": "Adjust Canvas for DTF",
                "severity": "medium",
                "current": f"{aspect_ratio.get('current_ratio_display', '?')} ({aspect_ratio.get('current_orientation', '?')})",
                "recommended": f"{top_rec['name']} ({top_rec['print_size']})" if top_rec else "Standard DTF ratio",
                "method": "AI Canvas Expansion or Smart Crop",
                "impact": "Optimizes artwork for standard DTF print sizes without distortion",
                "steps": [
                    f"Current ratio {aspect_ratio.get('current_ratio_display')} doesn't perfectly match standard DTF sizes",
                    f"Best match: {top_rec['name']} (score: {top_rec['score']}/100)" if top_rec else "Evaluate target sizes",
                    f"Option A: AI expand canvas by {top_rec['canvas_expand_pct']:.0f}% (generates new content)" if top_rec and top_rec.get('canvas_expand_pct', 0) > 0 else "Option A: Slight canvas expansion",
                    f"Option B: Smart crop losing {top_rec['crop_loss_pct']:.0f}% content" if top_rec and top_rec.get('crop_loss_pct', 0) > 0 else "Option B: Minimal crop",
                    "Choose based on subject position and client requirements",
                ],
                "auto_fixable": True,
            })

        # 4. Edge Refinement
        if decisions.get("needs_edge_refinement", {}).get("value"):
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "edges",
                "title": "Refine Edges",
                "severity": "medium",
                "current": "Rough or jagged edges detected",
                "recommended": "Smooth, clean edges suitable for cut-path generation",
                "method": "AI Edge Smoothing + Anti-aliasing",
                "impact": "Prevents visible jaggedness on printed transfer edges",
                "steps": [
                    "Detected rough edges on subject boundary",
                    "Apply AI edge refinement to smooth contours",
                    "Add 1-2px feather for natural blending on fabric",
                    "Verify no halo artifacts introduced",
                ],
                "auto_fixable": True,
            })

        # 5. Subject Positioning
        edge_contact = geometry.get("edge_contact", {})
        touching = [side for side, val in edge_contact.items() if val]
        if touching:
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "positioning",
                "title": "Add Safe Margins",
                "severity": "medium",
                "current": f"Subject touches: {', '.join(touching)}",
                "recommended": "Minimum 5% padding on all sides",
                "method": "AI Canvas Expansion (extend edges)",
                "impact": "Prevents content being cut off during DTF cutting/weeding process",
                "steps": [
                    f"Subject contacts canvas edge on: {', '.join(touching)}",
                    "Expand canvas to add breathing room around subject",
                    "AI will generate matching content to extend the design",
                    "Aim for at least 20px margin on all sides at final resolution",
                ],
                "auto_fixable": True,
            })

        # 6. Color Profile
        icc = file_inspection.get("icc_profile", "none")
        if icc == "none":
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "color",
                "title": "Embed Color Profile",
                "severity": "low",
                "current": "No ICC color profile embedded",
                "recommended": "sRGB IEC61966-2.1 profile embedded",
                "method": "Assign sRGB profile",
                "impact": "Ensures consistent color output across different printers",
                "steps": [
                    "File has no embedded color profile",
                    "Assign sRGB IEC61966-2.1 (standard web/print profile)",
                    "Do NOT convert colors, only assign the profile tag",
                    "This prevents color shifts during RIP processing",
                ],
                "auto_fixable": True,
            })

        # 7. Transparency Quality
        if has_alpha:
            transparent_pct = geometry.get("transparent_area_pct", 0)
            if transparent_pct < 5:
                priority_order += 1
                actions.append({
                    "priority": priority_order,
                    "category": "transparency",
                    "title": "Verify Transparency",
                    "severity": "low",
                    "current": f"Only {transparent_pct:.1f}% transparent area detected",
                    "recommended": "Clean transparency with no stray pixels",
                    "method": "Alpha channel cleanup",
                    "impact": "Ensures no unwanted white/colored artifacts print on fabric",
                    "steps": [
                        f"Alpha channel shows very little transparency ({transparent_pct:.1f}%)",
                        "Check if background was meant to be transparent",
                        "Remove any semi-transparent pixels at edges",
                        "Ensure all 'empty' areas are fully transparent (alpha = 0)",
                    ],
                    "auto_fixable": True,
                })

        # 8. File Format
        if extension not in ("png",):
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "format",
                "title": "Convert to PNG",
                "severity": "low",
                "current": f".{extension.upper()} format",
                "recommended": "PNG-24 with alpha channel",
                "method": "Format conversion",
                "impact": "PNG is the standard format for DTF production with transparency support",
                "steps": [
                    f"Current format ({extension.upper()}) may not support transparency or is lossy",
                    "Convert to PNG-24 with alpha channel",
                    "Ensure no JPEG compression artifacts carry over",
                    "Verify file size is reasonable (under 50MB for RIP software)",
                ],
                "auto_fixable": True,
            })

        # 9. Size Optimization for Target Product
        max_print_w = production.get("safe_print_width_inches", 0)
        max_print_h = production.get("safe_print_height_inches", 0)
        if max_print_w < 8 or max_print_h < 10:
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "size",
                "title": "Increase Print Size Capability",
                "severity": "high" if max_print_w < 4 else "medium",
                "current": f"Max safe print: {max_print_w}\" Ã— {max_print_h}\"",
                "recommended": "At least 10\" Ã— 14\" at 300 DPI for standard DTF",
                "method": "AI Upscale + Enhancement",
                "impact": "Enables printing at standard T-shirt sizes without quality loss",
                "steps": [
                    f"Current max print at 300 DPI: {max_print_w}\" Ã— {max_print_h}\"",
                    "This is too small for standard DTF front prints (10\" Ã— 14\")",
                    "Apply 2-4x AI super-resolution",
                    "Follow with AI sharpening to restore fine details",
                    f"Target: {max(10, max_print_w*2):.0f}\" Ã— {max(14, max_print_h*2):.0f}\" at 300 DPI",
                ],
                "auto_fixable": True,
            })

        # 10. Noise/Artifact Cleanup (if from JPEG)
        if extension in ("jpg", "jpeg"):
            priority_order += 1
            actions.append({
                "priority": priority_order,
                "category": "quality",
                "title": "Remove JPEG Artifacts",
                "severity": "low",
                "current": "JPEG compression artifacts likely present",
                "recommended": "Clean, artifact-free image",
                "method": "AI Denoising / Artifact Removal",
                "impact": "Prevents visible compression blocks in printed output",
                "steps": [
                    "JPEG format introduces compression artifacts (blocking, ringing)",
                    "Apply AI denoising to clean up compression artifacts",
                    "Use conservative settings to preserve intended detail",
                    "Convert to PNG after cleanup to prevent further degradation",
                ],
                "auto_fixable": True,
            })

        # Calculate overall improvement potential
        critical_count = sum(1 for a in actions if a["severity"] == "high")
        total_actions = len(actions)
        auto_fixable = sum(1 for a in actions if a.get("auto_fixable"))

        # Estimated final score after improvements
        current_score = production.get("production_score", 50)
        potential_improvement = min(30, critical_count * 10 + (total_actions - critical_count) * 3)
        estimated_final_score = min(100, current_score + potential_improvement)

        return {
            "actions": actions,
            "total_actions": total_actions,
            "critical_actions": critical_count,
            "auto_fixable_count": auto_fixable,
            "current_score": current_score,
            "estimated_final_score": estimated_final_score,
            "improvement_potential": potential_improvement,
            "production_ready": total_actions == 0,
            "summary": self._generate_summary(actions, current_score, estimated_final_score),
        }

    def _generate_summary(self, actions: list, current: int, estimated: int) -> str:
        if not actions:
            return "Artwork is production-ready. No improvements needed."
        high = [a for a in actions if a["severity"] == "high"]
        if high:
            return f"{len(high)} critical improvement(s) needed. Estimated score after fixes: {estimated}/100."
        return f"{len(actions)} improvement(s) recommended. Estimated score after fixes: {estimated}/100."
