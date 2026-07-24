"""Geometry Engine - spatial analysis using image properties."""

import io
from typing import Optional


class GeometryEngine:
    """Calculates geometry, spacing, and spatial relationships."""

    def analyze(self, file_bytes: bytes, extension: str, width: int, height: int, has_alpha: bool) -> dict:
        """Perform geometry analysis."""
        result = {
            "bounding_box": {"x": 0, "y": 0, "width": width, "height": height},
            "subject_coverage_pct": 100.0,
            "canvas_usage_pct": 100.0,
            "empty_space_pct": 0.0,
            "transparent_area_pct": 0.0,
            "safe_margins": {"top": 0, "right": 0, "bottom": 0, "left": 0},
            "cropping_risk": False,
            "edge_contact": {"top": False, "right": False, "bottom": False, "left": False},
            "rotation": 0,
            "aspect_ratio": round(width / height, 3) if height > 0 else 1.0,
            "subject_centered": True,
        }

        if extension in ("png", "jpg", "jpeg", "webp", "tiff", "tif", "bmp"):
            result = self._analyze_raster_geometry(file_bytes, width, height, has_alpha, result)

        return result

    def _analyze_raster_geometry(self, file_bytes: bytes, width: int, height: int, has_alpha: bool, result: dict) -> dict:
        """Analyze raster image geometry."""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))

            if has_alpha and img.mode == "RGBA":
                # Analyze alpha channel to find subject bounds
                alpha = img.split()[3]
                bbox = alpha.getbbox()

                if bbox:
                    bx, by, bx2, by2 = bbox
                    bw = bx2 - bx
                    bh = by2 - by

                    result["bounding_box"] = {"x": bx, "y": by, "width": bw, "height": bh}
                    result["subject_coverage_pct"] = round((bw * bh) / (width * height) * 100, 1)
                    result["canvas_usage_pct"] = result["subject_coverage_pct"]
                    result["empty_space_pct"] = round(100 - result["subject_coverage_pct"], 1)

                    # Transparent area
                    from PIL import ImageStat
                    alpha_stat = ImageStat.Stat(alpha)
                    avg_alpha = alpha_stat.mean[0]
                    result["transparent_area_pct"] = round((255 - avg_alpha) / 255 * 100, 1)

                    # Safe margins (distance from subject to edge in pixels)
                    result["safe_margins"] = {
                        "top": by,
                        "right": width - bx2,
                        "bottom": height - by2,
                        "left": bx,
                    }

                    # Edge contact detection (subject touching within 5px of border)
                    threshold = 5
                    result["edge_contact"] = {
                        "top": by < threshold,
                        "right": (width - bx2) < threshold,
                        "bottom": (height - by2) < threshold,
                        "left": bx < threshold,
                    }

                    # Cropping risk
                    result["cropping_risk"] = any(result["edge_contact"].values())

                    # Subject centering
                    center_x = bx + bw / 2
                    center_y = by + bh / 2
                    canvas_center_x = width / 2
                    canvas_center_y = height / 2
                    x_offset = abs(center_x - canvas_center_x) / width
                    y_offset = abs(center_y - canvas_center_y) / height
                    result["subject_centered"] = x_offset < 0.1 and y_offset < 0.1

                else:
                    # Fully transparent
                    result["subject_coverage_pct"] = 0
                    result["transparent_area_pct"] = 100
                    result["empty_space_pct"] = 100
            else:
                # No alpha - assume full canvas usage
                result["subject_coverage_pct"] = 100.0
                result["canvas_usage_pct"] = 100.0

                # Check for uniform border (potential padding)
                pixels = img.load()
                # Sample top-left corner color
                corner_color = pixels[0, 0] if img.mode == "RGB" else pixels[0, 0][:3] if img.mode in ("RGBA",) else (255, 255, 255)

                # Simple edge analysis - check if edges are uniform
                edge_uniform_top = all(
                    self._colors_similar(pixels[x, 0], corner_color, img.mode)
                    for x in range(0, width, max(1, width // 20))
                )
                if edge_uniform_top:
                    result["safe_margins"]["top"] = self._measure_margin(img, "top", corner_color)
                    result["safe_margins"]["bottom"] = self._measure_margin(img, "bottom", corner_color)
                    result["safe_margins"]["left"] = self._measure_margin(img, "left", corner_color)
                    result["safe_margins"]["right"] = self._measure_margin(img, "right", corner_color)

                    total_margin_area = (
                        (result["safe_margins"]["top"] + result["safe_margins"]["bottom"]) * width +
                        (result["safe_margins"]["left"] + result["safe_margins"]["right"]) * height
                    )
                    result["empty_space_pct"] = round(total_margin_area / (width * height) * 100, 1)
                    result["subject_coverage_pct"] = round(100 - result["empty_space_pct"], 1)

            img.close()

        except Exception:
            pass

        return result

    def _colors_similar(self, c1, c2, mode: str, threshold: int = 20) -> bool:
        """Check if two colors are similar."""
        try:
            if mode == "RGB":
                return all(abs(a - b) < threshold for a, b in zip(c1, c2))
            elif mode == "RGBA":
                return all(abs(a - b) < threshold for a, b in zip(c1[:3], c2[:3]))
            return abs(c1 - c2) < threshold
        except (TypeError, IndexError):
            return False

    def _measure_margin(self, img, side: str, bg_color, max_check: int = 100) -> int:
        """Measure margin from an edge."""
        width, height = img.size
        pixels = img.load()
        mode = img.mode

        for i in range(min(max_check, width if side in ("left", "right") else height)):
            if side == "top":
                row_same = all(
                    self._colors_similar(pixels[x, i], bg_color, mode)
                    for x in range(0, width, max(1, width // 10))
                )
            elif side == "bottom":
                row_same = all(
                    self._colors_similar(pixels[x, height - 1 - i], bg_color, mode)
                    for x in range(0, width, max(1, width // 10))
                )
            elif side == "left":
                row_same = all(
                    self._colors_similar(pixels[i, y], bg_color, mode)
                    for y in range(0, height, max(1, height // 10))
                )
            else:  # right
                row_same = all(
                    self._colors_similar(pixels[width - 1 - i, y], bg_color, mode)
                    for y in range(0, height, max(1, height // 10))
                )

            if not row_same:
                return i

        return 0
