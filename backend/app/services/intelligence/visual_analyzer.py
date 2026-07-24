"""Visual Analysis Engine - semantic understanding of artwork content.

In production, this would call GPT-5.5 Vision or equivalent.
For local development, it uses heuristic analysis based on image properties.
"""

import io
from typing import Optional


class VisualAnalyzer:
    """Analyzes visual content, composition, and artistic properties."""

    def analyze(self, file_bytes: bytes, extension: str, metadata: dict) -> dict:
        """Perform visual analysis. Returns structured analysis."""
        result = {
            "artwork_type": "unknown",
            "artwork_type_confidence": 0.0,
            "subjects": [],
            "composition": {},
            "typography": {},
            "background": {},
            "artistic_style": "unknown",
            "style_confidence": 0.0,
            "color_analysis": {},
        }

        if extension in ("png", "jpg", "jpeg", "webp", "tiff", "tif", "bmp"):
            result = self._analyze_raster(file_bytes, metadata, result)
        elif extension == "svg":
            result = self._analyze_vector(file_bytes, result)
        else:
            result["artwork_type"] = "document"
            result["artwork_type_confidence"] = 0.5

        return result

    def _analyze_raster(self, file_bytes: bytes, metadata: dict, result: dict) -> dict:
        """Analyze raster image content."""
        try:
            from PIL import Image, ImageStat
            img = Image.open(io.BytesIO(file_bytes))

            width, height = img.width, img.height
            has_alpha = img.mode in ("RGBA", "LA", "PA")

            # Convert to RGB for analysis
            if img.mode == "RGBA":
                rgb_img = img.convert("RGB")
                alpha_channel = img.split()[3]
            elif img.mode != "RGB":
                rgb_img = img.convert("RGB")
                alpha_channel = None
            else:
                rgb_img = img
                alpha_channel = None

            # Color analysis
            stat = ImageStat.Stat(rgb_img)
            avg_color = tuple(int(c) for c in stat.mean)
            color_variance = sum(stat.var) / 3

            result["color_analysis"] = {
                "average_color_rgb": list(avg_color),
                "color_variance": round(color_variance, 2),
                "is_monochrome": color_variance < 500,
                "dominant_tone": self._classify_tone(avg_color),
                "color_complexity": "high" if color_variance > 3000 else "medium" if color_variance > 800 else "low",
            }

            # Artwork type heuristics
            aspect_ratio = width / height if height > 0 else 1
            is_square_ish = 0.8 <= aspect_ratio <= 1.2
            is_small = width < 500 and height < 500

            if has_alpha and is_square_ish and is_small:
                result["artwork_type"] = "logo"
                result["artwork_type_confidence"] = 0.7
            elif has_alpha and is_square_ish:
                result["artwork_type"] = "illustration"
                result["artwork_type_confidence"] = 0.65
            elif has_alpha:
                result["artwork_type"] = "sticker"
                result["artwork_type_confidence"] = 0.6
            elif color_variance > 5000:
                result["artwork_type"] = "photo"
                result["artwork_type_confidence"] = 0.6
            elif color_variance < 500:
                result["artwork_type"] = "text_design"
                result["artwork_type_confidence"] = 0.55
            else:
                result["artwork_type"] = "illustration"
                result["artwork_type_confidence"] = 0.5

            # Composition analysis
            result["composition"] = {
                "aspect_ratio": round(aspect_ratio, 3),
                "orientation": "landscape" if aspect_ratio > 1.2 else "portrait" if aspect_ratio < 0.8 else "square",
                "is_centered": True,  # Heuristic: assume centered for now
                "layout": "centered" if is_square_ish else "wide" if aspect_ratio > 1.5 else "tall",
            }

            # Background analysis
            if has_alpha and alpha_channel:
                # Check how much of the image is transparent
                alpha_stat = ImageStat.Stat(alpha_channel)
                avg_alpha = alpha_stat.mean[0]
                if avg_alpha < 200:
                    transparent_pct = round((255 - avg_alpha) / 255 * 100, 1)
                    result["background"] = {
                        "type": "transparent",
                        "transparent_percentage": transparent_pct,
                        "removable": False,
                        "complexity": "none",
                    }
                else:
                    result["background"] = {
                        "type": "solid",
                        "transparent_percentage": 0,
                        "removable": True,
                        "complexity": "low",
                    }
            else:
                # Check edge pixels for solid background detection
                result["background"] = {
                    "type": "complex" if color_variance > 2000 else "solid",
                    "transparent_percentage": 0,
                    "removable": color_variance < 3000,
                    "complexity": "high" if color_variance > 3000 else "medium" if color_variance > 1000 else "low",
                }

            # Typography detection (basic heuristic)
            result["typography"] = {
                "has_text": False,  # Would need OCR/Vision API for real detection
                "text_blocks": 0,
                "decorative_text": False,
                "curved_text": False,
                "editable": False,
                "font_complexity": "unknown",
                "small_text_risk": False,
            }

            # Artistic style
            if color_variance < 300:
                result["artistic_style"] = "minimal"
            elif color_variance > 5000:
                result["artistic_style"] = "realistic"
            elif has_alpha:
                result["artistic_style"] = "vector"
            else:
                result["artistic_style"] = "modern"
            result["style_confidence"] = 0.5

            # Subject detection
            result["subjects"] = [{
                "type": "primary",
                "label": result["artwork_type"],
                "confidence": result["artwork_type_confidence"],
                "bounding_box": {"x": 0, "y": 0, "w": width, "h": height},
            }]

            img.close()

        except Exception as e:
            result["artwork_type"] = "unknown"
            result["artwork_type_confidence"] = 0.0

        return result

    def _analyze_vector(self, file_bytes: bytes, result: dict) -> dict:
        """Analyze vector artwork."""
        result["artwork_type"] = "vector"
        result["artwork_type_confidence"] = 0.9
        result["artistic_style"] = "vector"
        result["style_confidence"] = 0.9
        result["background"] = {"type": "transparent", "transparent_percentage": 100, "removable": False, "complexity": "none"}
        result["composition"] = {"layout": "centered", "orientation": "square", "is_centered": True}
        return result

    def _classify_tone(self, rgb: tuple) -> str:
        r, g, b = rgb
        brightness = (r + g + b) / 3
        if brightness > 200:
            return "light"
        elif brightness < 60:
            return "dark"
        elif r > g and r > b:
            return "warm"
        elif b > r and b > g:
            return "cool"
        return "neutral"
