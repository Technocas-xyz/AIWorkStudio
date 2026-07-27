"""Image Quality Analyzer - detects halftone, blackout, noise, banding, and other print quality issues."""

import io
import math
from typing import Optional


class ImageQualityAnalyzer:
    """Deep image quality analysis for DTF print production."""

    def analyze(self, file_bytes: bytes, extension: str, width: int, height: int, has_alpha: bool) -> dict:
        """Run comprehensive image quality analysis."""
        result = {
            "overall_quality": "unknown",
            "quality_score": 0,
            "issues": [],
            "halftone": {"detected": False, "confidence": 0, "severity": "none"},
            "blackout": {"detected": False, "areas_pct": 0, "severity": "none"},
            "whiteout": {"detected": False, "areas_pct": 0, "severity": "none"},
            "noise": {"detected": False, "level": "none", "severity": "none"},
            "banding": {"detected": False, "type": "none", "severity": "none"},
            "blur": {"detected": False, "sharpness_score": 0, "severity": "none"},
            "jpeg_artifacts": {"detected": False, "severity": "none"},
            "posterization": {"detected": False, "severity": "none"},
            "color_clipping": {"highlights_clipped": False, "shadows_clipped": False, "severity": "none"},
            "edge_quality": {"halos": False, "fringing": False, "jagged": False, "severity": "none"},
            "contrast": {"level": "normal", "ratio": 0, "severity": "none"},
            "saturation": {"level": "normal", "avg_saturation": 0, "severity": "none"},
            "dynamic_range": {"range": 0, "quality": "normal"},
        }

        if extension not in ("png", "jpg", "jpeg", "webp", "tiff", "tif", "bmp"):
            result["overall_quality"] = "not_analyzed"
            result["quality_score"] = 50
            return result

        try:
            from PIL import Image, ImageStat, ImageFilter

            img = Image.open(io.BytesIO(file_bytes))

            # Convert to RGB for analysis
            if img.mode == "RGBA":
                rgb_img = img.convert("RGB")
            elif img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img

            # Get grayscale for luminance analysis
            gray = rgb_img.convert("L")
            gray_stat = ImageStat.Stat(gray)
            rgb_stat = ImageStat.Stat(rgb_img)

            # === BLACKOUT DETECTION ===
            result["blackout"] = self._detect_blackout(gray, gray_stat, width, height)

            # === WHITEOUT DETECTION ===
            result["whiteout"] = self._detect_whiteout(gray, gray_stat, width, height)

            # === HALFTONE DETECTION ===
            result["halftone"] = self._detect_halftone(gray, width, height)

            # === NOISE DETECTION ===
            result["noise"] = self._detect_noise(gray, rgb_img)

            # === BLUR / SHARPNESS ===
            result["blur"] = self._detect_blur(gray)

            # === BANDING DETECTION ===
            result["banding"] = self._detect_banding(gray, width, height)

            # === JPEG ARTIFACTS ===
            result["jpeg_artifacts"] = self._detect_jpeg_artifacts(extension, gray)

            # === POSTERIZATION ===
            result["posterization"] = self._detect_posterization(gray)

            # === COLOR CLIPPING ===
            result["color_clipping"] = self._detect_color_clipping(gray_stat)

            # === EDGE QUALITY ===
            if has_alpha:
                alpha = img.split()[3] if img.mode == "RGBA" else None
                result["edge_quality"] = self._detect_edge_issues(rgb_img, alpha)
            else:
                result["edge_quality"] = {"halos": False, "fringing": False, "jagged": False, "severity": "none"}

            # === CONTRAST ===
            result["contrast"] = self._analyze_contrast(gray_stat)

            # === SATURATION ===
            result["saturation"] = self._analyze_saturation(rgb_img)

            # === DYNAMIC RANGE ===
            result["dynamic_range"] = self._analyze_dynamic_range(gray_stat)

            # === OVERALL QUALITY SCORE ===
            result["quality_score"] = self._calculate_quality_score(result)
            result["overall_quality"] = self._quality_label(result["quality_score"])

            # === COLLECT ISSUES ===
            result["issues"] = self._collect_issues(result)

            img.close()

        except Exception as e:
            result["overall_quality"] = "error"
            result["quality_score"] = 0
            result["issues"] = [{"title": "Analysis Error", "detail": str(e), "severity": "high"}]

        return result

    def _detect_blackout(self, gray, gray_stat, width: int, height: int) -> dict:
        """Detect large solid black areas (ink waste / visibility issues)."""
        histogram = gray.histogram()
        # Count pixels in very dark range (0-15)
        dark_pixels = sum(histogram[:16])
        total_pixels = width * height
        dark_pct = (dark_pixels / total_pixels) * 100 if total_pixels > 0 else 0

        detected = dark_pct > 30
        severity = "critical" if dark_pct > 60 else "high" if dark_pct > 40 else "medium" if dark_pct > 30 else "none"

        return {"detected": detected, "areas_pct": round(dark_pct, 1), "severity": severity}

    def _detect_whiteout(self, gray, gray_stat, width: int, height: int) -> dict:
        """Detect large solid white areas (wasted film / no ink)."""
        histogram = gray.histogram()
        # Count pixels in very bright range (240-255)
        bright_pixels = sum(histogram[240:])
        total_pixels = width * height
        bright_pct = (bright_pixels / total_pixels) * 100 if total_pixels > 0 else 0

        detected = bright_pct > 40
        severity = "medium" if bright_pct > 60 else "low" if bright_pct > 40 else "none"

        return {"detected": detected, "areas_pct": round(bright_pct, 1), "severity": severity}

    def _detect_halftone(self, gray, width: int, height: int) -> dict:
        """Detect halftone dot patterns (scanned print / newspaper source)."""
        try:
            from PIL import ImageFilter
            # Halftone creates high-frequency regular patterns
            # Apply edge detection and look for periodic structures
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)

            # High mean edge value with low variance suggests regular pattern (halftone)
            edge_mean = edge_stat.mean[0]
            edge_var = edge_stat.var[0]

            # Halftone typically has moderate edge mean (dots everywhere) with relatively consistent variance
            # A photo has localized edges with high variance
            regularity = edge_mean / (math.sqrt(edge_var) + 1)

            detected = regularity > 1.5 and edge_mean > 20
            confidence = min(1.0, regularity / 3.0) if detected else 0

            severity = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low" if detected else "none"

            return {"detected": detected, "confidence": round(confidence, 2), "severity": severity,
                    "detail": "Regular dot pattern detected - likely scanned from printed material" if detected else "No halftone pattern"}
        except Exception:
            return {"detected": False, "confidence": 0, "severity": "none"}

    def _detect_noise(self, gray, rgb_img) -> dict:
        """Detect image noise (sensor noise, film grain, compression noise)."""
        try:
            from PIL import ImageFilter, ImageStat
            # Compare original with smoothed version
            smoothed = gray.filter(ImageFilter.GaussianBlur(2))

            # Calculate difference
            from PIL import ImageChops
            diff = ImageChops.difference(gray, smoothed)
            diff_stat = ImageStat.Stat(diff)
            noise_level = diff_stat.mean[0]

            if noise_level > 12:
                detected, level, severity = True, "high", "high"
            elif noise_level > 7:
                detected, level, severity = True, "moderate", "medium"
            elif noise_level > 4:
                detected, level, severity = True, "low", "low"
            else:
                detected, level, severity = False, "minimal", "none"

            return {"detected": detected, "level": level, "noise_value": round(noise_level, 2), "severity": severity}
        except Exception:
            return {"detected": False, "level": "unknown", "severity": "none"}

    def _detect_blur(self, gray) -> dict:
        """Detect blur / lack of sharpness using Laplacian variance."""
        try:
            from PIL import ImageFilter, ImageStat
            laplacian = gray.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
            lap_stat = ImageStat.Stat(laplacian)
            sharpness = lap_stat.var[0]

            # Higher variance = sharper image
            if sharpness > 1000:
                quality = "very_sharp"
                severity = "none"
            elif sharpness > 500:
                quality = "sharp"
                severity = "none"
            elif sharpness > 200:
                quality = "moderate"
                severity = "low"
            elif sharpness > 80:
                quality = "soft"
                severity = "medium"
            else:
                quality = "blurry"
                severity = "high"

            detected = sharpness < 200
            return {"detected": detected, "sharpness_score": round(sharpness, 1), "quality": quality, "severity": severity}
        except Exception:
            return {"detected": False, "sharpness_score": 0, "severity": "none"}

    def _detect_banding(self, gray, width: int, height: int) -> dict:
        """Detect color/tone banding (gradient stepping)."""
        try:
            histogram = gray.histogram()
            # Look for gaps in the histogram (missing tones = banding)
            zero_runs = 0
            max_run = 0
            current_run = 0

            for count in histogram[10:245]:  # Skip extremes
                if count == 0:
                    current_run += 1
                else:
                    if current_run > 0:
                        zero_runs += 1
                        max_run = max(max_run, current_run)
                    current_run = 0

            detected = zero_runs > 20 or max_run > 5
            severity = "high" if max_run > 10 else "medium" if max_run > 5 else "low" if detected else "none"
            band_type = "gradient_stepping" if detected else "none"

            return {"detected": detected, "type": band_type, "gap_count": zero_runs, "max_gap": max_run, "severity": severity}
        except Exception:
            return {"detected": False, "type": "none", "severity": "none"}

    def _detect_jpeg_artifacts(self, extension: str, gray) -> dict:
        """Detect JPEG compression artifacts (blocking, ringing)."""
        if extension not in ("jpg", "jpeg"):
            return {"detected": False, "severity": "none", "detail": "Non-JPEG format"}

        try:
            from PIL import ImageFilter, ImageStat
            # JPEG artifacts show as 8x8 block boundaries
            # Detect by looking at high-frequency content along grid lines
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_intensity = edge_stat.mean[0]

            # High edge content in JPEG usually indicates visible artifacts
            if edge_intensity > 15:
                severity = "high"
            elif edge_intensity > 8:
                severity = "medium"
            else:
                severity = "low"

            return {"detected": True, "severity": severity,
                    "detail": f"JPEG format - compression artifacts likely (edge intensity: {edge_intensity:.1f})"}
        except Exception:
            return {"detected": True, "severity": "low", "detail": "JPEG format detected"}

    def _detect_posterization(self, gray) -> dict:
        """Detect posterization (reduced color levels / flat areas)."""
        try:
            histogram = gray.histogram()
            # Count unique tone levels with significant pixel count
            significant_levels = sum(1 for count in histogram if count > 100)

            if significant_levels < 32:
                detected, severity = True, "high"
            elif significant_levels < 64:
                detected, severity = True, "medium"
            elif significant_levels < 128:
                detected, severity = True, "low"
            else:
                detected, severity = False, "none"

            return {"detected": detected, "unique_levels": significant_levels, "severity": severity}
        except Exception:
            return {"detected": False, "severity": "none"}

    def _detect_color_clipping(self, gray_stat) -> dict:
        """Detect highlight/shadow clipping (loss of detail in extremes)."""
        mean = gray_stat.mean[0]
        stddev = math.sqrt(gray_stat.var[0])

        # Shadow clipping: mean very low with low stddev
        shadows_clipped = mean < 40 and stddev < 30
        # Highlight clipping: mean very high with low stddev
        highlights_clipped = mean > 220 and stddev < 30

        severity = "high" if (shadows_clipped and highlights_clipped) else "medium" if (shadows_clipped or highlights_clipped) else "none"

        return {"highlights_clipped": highlights_clipped, "shadows_clipped": shadows_clipped, "severity": severity}

    def _detect_edge_issues(self, rgb_img, alpha) -> dict:
        """Detect edge artifacts: halos, fringing, jagged edges."""
        halos = False
        fringing = False
        jagged = False

        try:
            if alpha:
                from PIL import ImageFilter, ImageStat, ImageChops
                # Check for halos by looking at bright pixels near alpha edges
                alpha_edges = alpha.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(alpha_edges)

                # High edge variance on alpha = potential jagged edges
                if edge_stat.var[0] > 3000:
                    jagged = True

                # Check for white/bright fringe near edges
                # Dilate alpha slightly and check the difference area
                dilated = alpha.filter(ImageFilter.MaxFilter(3))
                fringe_area = ImageChops.difference(dilated, alpha)
                fringe_stat = ImageStat.Stat(fringe_area)
                if fringe_stat.mean[0] > 10:
                    halos = True

        except Exception:
            pass

        severity = "high" if (halos and jagged) else "medium" if (halos or fringing or jagged) else "none"
        return {"halos": halos, "fringing": fringing, "jagged": jagged, "severity": severity}

    def _analyze_contrast(self, gray_stat) -> dict:
        """Analyze contrast levels."""
        stddev = math.sqrt(gray_stat.var[0])
        mean = gray_stat.mean[0]

        if stddev > 80:
            level = "very_high"
            severity = "low"  # May lose detail in shadows/highlights
        elif stddev > 55:
            level = "high"
            severity = "none"
        elif stddev > 35:
            level = "normal"
            severity = "none"
        elif stddev > 20:
            level = "low"
            severity = "medium"
        else:
            level = "very_low"
            severity = "high"

        return {"level": level, "stddev": round(stddev, 1), "mean_brightness": round(mean, 1), "severity": severity}

    def _analyze_saturation(self, rgb_img) -> dict:
        """Analyze color saturation levels."""
        try:
            hsv = rgb_img.convert("HSV")
            s_channel = hsv.split()[1]
            from PIL import ImageStat
            s_stat = ImageStat.Stat(s_channel)
            avg_sat = s_stat.mean[0]

            if avg_sat > 180:
                level, severity = "oversaturated", "medium"
            elif avg_sat > 130:
                level, severity = "vibrant", "none"
            elif avg_sat > 60:
                level, severity = "normal", "none"
            elif avg_sat > 25:
                level, severity = "desaturated", "low"
            else:
                level, severity = "near_monochrome", "none"

            return {"level": level, "avg_saturation": round(avg_sat, 1), "severity": severity}
        except Exception:
            return {"level": "unknown", "avg_saturation": 0, "severity": "none"}

    def _analyze_dynamic_range(self, gray_stat) -> dict:
        """Analyze tonal dynamic range."""
        min_val = gray_stat.extrema[0][0]
        max_val = gray_stat.extrema[0][1]
        dyn_range = max_val - min_val

        if dyn_range > 230:
            quality = "excellent"
        elif dyn_range > 180:
            quality = "good"
        elif dyn_range > 120:
            quality = "moderate"
        else:
            quality = "limited"

        return {"range": dyn_range, "min": min_val, "max": max_val, "quality": quality}

    def _calculate_quality_score(self, result: dict) -> int:
        """Calculate overall quality score 0-100."""
        score = 100

        # Penalties
        severity_penalty = {"critical": 25, "high": 15, "medium": 8, "low": 3, "none": 0}

        score -= severity_penalty.get(result["blackout"]["severity"], 0)
        score -= severity_penalty.get(result["whiteout"]["severity"], 0)
        score -= severity_penalty.get(result["halftone"]["severity"], 0)
        score -= severity_penalty.get(result["noise"]["severity"], 0)
        score -= severity_penalty.get(result["blur"]["severity"], 0)
        score -= severity_penalty.get(result["banding"]["severity"], 0)
        score -= severity_penalty.get(result["jpeg_artifacts"]["severity"], 0)
        score -= severity_penalty.get(result["posterization"]["severity"], 0)
        score -= severity_penalty.get(result["color_clipping"]["severity"], 0)
        score -= severity_penalty.get(result["edge_quality"]["severity"], 0)
        score -= severity_penalty.get(result["contrast"]["severity"], 0)
        score -= severity_penalty.get(result["saturation"]["severity"], 0)

        return max(0, min(100, score))

    def _quality_label(self, score: int) -> str:
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 55:
            return "fair"
        elif score >= 35:
            return "poor"
        return "bad"

    def _collect_issues(self, result: dict) -> list:
        """Collect all detected issues into a flat list."""
        issues = []

        if result["blackout"]["detected"]:
            issues.append({"title": "Blackout Areas", "detail": f"{result['blackout']['areas_pct']}% of image is solid black - heavy ink usage, may bleed on fabric", "severity": result["blackout"]["severity"]})

        if result["whiteout"]["detected"]:
            issues.append({"title": "Whiteout Areas", "detail": f"{result['whiteout']['areas_pct']}% of image is solid white - wasted film if not transparent", "severity": result["whiteout"]["severity"]})

        if result["halftone"]["detected"]:
            issues.append({"title": "Halftone Pattern", "detail": f"Dot pattern detected ({result['halftone']['confidence']:.0%} confidence) - likely scanned from print. Will produce moirÃ© on DTF.", "severity": result["halftone"]["severity"]})

        if result["noise"]["detected"]:
            issues.append({"title": f"Image Noise ({result['noise']['level'].capitalize()})", "detail": f"Noise level: {result['noise'].get('noise_value', 0)} - will appear as grain/specks when printed", "severity": result["noise"]["severity"]})

        if result["blur"]["detected"]:
            issues.append({"title": f"Image Softness ({result['blur'].get('quality', 'soft')})", "detail": f"Sharpness score: {result['blur']['sharpness_score']} - design will lack crisp edges when printed", "severity": result["blur"]["severity"]})

        if result["banding"]["detected"]:
            issues.append({"title": "Color Banding", "detail": f"Gradient stepping detected ({result['banding'].get('gap_count', 0)} gaps) - smooth gradients will show visible steps", "severity": result["banding"]["severity"]})

        if result["jpeg_artifacts"]["detected"] and result["jpeg_artifacts"]["severity"] != "none":
            issues.append({"title": "JPEG Compression Artifacts", "detail": result["jpeg_artifacts"].get("detail", "Block artifacts from lossy compression"), "severity": result["jpeg_artifacts"]["severity"]})

        if result["posterization"]["detected"]:
            issues.append({"title": "Posterization", "detail": f"Only {result['posterization'].get('unique_levels', 0)} tone levels - flat areas where smooth gradients should be", "severity": result["posterization"]["severity"]})

        if result["color_clipping"]["shadows_clipped"]:
            issues.append({"title": "Shadow Clipping", "detail": "Dark areas have lost detail - all crushed to pure black", "severity": "medium"})

        if result["color_clipping"]["highlights_clipped"]:
            issues.append({"title": "Highlight Clipping", "detail": "Bright areas have lost detail - all blown to pure white", "severity": "medium"})

        if result["edge_quality"]["halos"]:
            issues.append({"title": "Edge Halos", "detail": "Bright/white fringe around subject edges - visible on colored garments", "severity": "medium"})

        if result["edge_quality"]["jagged"]:
            issues.append({"title": "Jagged Edges", "detail": "Rough/aliased edges on subject boundary - will look pixelated", "severity": "medium"})

        if result["contrast"]["severity"] != "none":
            issues.append({"title": f"Contrast ({result['contrast']['level'].replace('_', ' ').capitalize()})", "detail": f"Stddev: {result['contrast']['stddev']} - may appear washed out or overly dark", "severity": result["contrast"]["severity"]})

        if result["saturation"]["severity"] != "none":
            issues.append({"title": f"Saturation ({result['saturation']['level'].replace('_', ' ').capitalize()})", "detail": f"Avg saturation: {result['saturation']['avg_saturation']} - colors may not reproduce accurately", "severity": result["saturation"]["severity"]})

        return issues
