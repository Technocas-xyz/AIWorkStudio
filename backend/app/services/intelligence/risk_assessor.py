"""Risk Assessment Engine - identifies production risks."""


class RiskAssessor:
    """Identifies and classifies production risks."""

    def assess(self, file_inspection: dict, visual: dict, geometry: dict,
               production: dict, width: int, height: int, dpi: int, has_alpha: bool) -> dict:
        """Perform comprehensive risk assessment."""
        risks = []

        # Resolution risks
        if dpi and dpi < 200:
            risks.append({
                "id": "low_resolution",
                "severity": "critical" if dpi < 100 else "high",
                "title": "Below Minimum Print DPI",
                "description": f"Image DPI ({dpi}) is below the minimum 200 DPI required for DTF production. Target is 300 DPI.",
                "impact": "Will result in pixelated, blurry, or unprofessional output when printed.",
                "recommendation": "Apply AI super-resolution upscale. Minimum 200 DPI required, 300 DPI recommended.",
            })
        elif dpi and dpi < 300:
            risks.append({
                "id": "suboptimal_resolution",
                "severity": "medium",
                "title": "Below Recommended DPI",
                "description": f"Image DPI ({dpi}) meets minimum (200) but is below recommended 300 DPI.",
                "impact": "Acceptable quality but fine details may not be crisp at full print size.",
                "recommendation": "Consider AI upscale to reach 300 DPI for best results.",
            })

        if width and height and (width < 500 or height < 500):
            risks.append({
                "id": "small_dimensions",
                "severity": "high" if (width < 200 or height < 200) else "medium",
                "title": "Small Image Dimensions",
                "description": f"Image is only {width}×{height}px.",
                "impact": "Enlargement will cause quality loss.",
                "recommendation": "Use AI upscaling to increase dimensions before production.",
            })

        # Geometry risks
        if geometry.get("cropping_risk"):
            edge_contact = geometry.get("edge_contact", {})
            touching = [side for side, val in edge_contact.items() if val]
            risks.append({
                "id": "edge_contact",
                "severity": "medium",
                "title": "Subject Touches Edge",
                "description": f"Subject contacts canvas edge on: {', '.join(touching)}.",
                "impact": "May cause cropping issues during production.",
                "recommendation": "Add canvas padding or reposition subject.",
            })

        if geometry.get("subject_coverage_pct", 100) < 30:
            risks.append({
                "id": "low_coverage",
                "severity": "low",
                "title": "Low Canvas Usage",
                "description": f"Subject only covers {geometry.get('subject_coverage_pct', 0):.0f}% of canvas.",
                "impact": "Excessive whitespace may waste material.",
                "recommendation": "Crop canvas to subject bounds.",
            })

        # Transparency risks
        if not has_alpha:
            bg_type = visual.get("background", {}).get("type", "unknown")
            if bg_type == "complex":
                risks.append({
                    "id": "complex_background",
                    "severity": "high",
                    "title": "Complex Background Without Transparency",
                    "description": "Image has a complex background and no alpha channel.",
                    "impact": "Background removal may be difficult and result in artifacts.",
                    "recommendation": "Use AI background removal with manual refinement.",
                })
            elif bg_type == "solid":
                risks.append({
                    "id": "solid_background",
                    "severity": "low",
                    "title": "Solid Background (No Transparency)",
                    "description": "Image has a solid background that may need removal.",
                    "impact": "Minor - solid backgrounds are easy to remove.",
                    "recommendation": "Apply automated background removal.",
                })

        # Detail risks
        if production.get("fine_detail_score", 100) < 40:
            risks.append({
                "id": "low_detail",
                "severity": "medium",
                "title": "Low Fine Detail",
                "description": "Image lacks fine detail for production.",
                "impact": "May appear soft or blurry in final product.",
                "recommendation": "Apply sharpening or AI enhancement.",
            })

        if production.get("small_text_risk"):
            risks.append({
                "id": "small_text",
                "severity": "medium",
                "title": "Small Text Risk",
                "description": "Image resolution may not support legible small text.",
                "impact": "Text may become unreadable at production size.",
                "recommendation": "Increase resolution or enlarge text elements.",
            })

        # File issues
        for issue in file_inspection.get("issues", []):
            if "corrupt" in issue.lower():
                risks.append({
                    "id": "file_corrupt",
                    "severity": "critical",
                    "title": "File Integrity Issue",
                    "description": issue,
                    "impact": "File may not process correctly.",
                    "recommendation": "Re-upload or repair the file.",
                })
            elif "profile" in issue.lower():
                risks.append({
                    "id": "missing_profile",
                    "severity": "low",
                    "title": "Missing Color Profile",
                    "description": issue,
                    "impact": "Colors may shift during production.",
                    "recommendation": "Embed sRGB color profile.",
                })

        # Calculate overall risk level
        severities = [r["severity"] for r in risks]
        if "critical" in severities:
            risk_level = "critical"
        elif severities.count("high") >= 2:
            risk_level = "high"
        elif "high" in severities:
            risk_level = "medium"
        elif "medium" in severities:
            risk_level = "low"
        else:
            risk_level = "minimal"

        return {
            "risks": risks,
            "risk_count": len(risks),
            "risk_level": risk_level,
            "critical_count": severities.count("critical"),
            "high_count": severities.count("high"),
            "medium_count": severities.count("medium"),
            "low_count": severities.count("low"),
        }
