"""GPT Vision Analyzer - uses OpenAI GPT-5.5 Vision for semantic artwork understanding."""

import base64
import io
import json
import os
from typing import Optional
from dotenv import load_dotenv

# Load .env from project root
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
load_dotenv(os.path.join(_root, ".env"))


class GPTVisualAnalyzer:
    """Analyzes artwork using OpenAI GPT-5.5 Vision API."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        """Check if the API key is configured."""
        return bool(self.api_key and self.api_key != "your-openai-api-key-here")

    def analyze(self, file_bytes: bytes, extension: str, metadata: dict) -> dict:
        """Perform visual analysis using GPT-4o Vision."""
        if not self.is_available():
            return {
                "error": "OpenAI API key not configured. Add OPENAI_API_KEY to your .env file.",
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

        # Encode image to base64
        b64_image = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = f"image/{extension}" if extension in ("png", "jpg", "jpeg", "webp", "gif") else "image/png"

        # Build technical context from Pillow data
        tech_context = ""
        if metadata:
            tech_lines = ["TECHNICAL DATA (from pixel analysis):"]
            if metadata.get("width"):
                tech_lines.append(f"- Dimensions: {metadata.get('width')}×{metadata.get('height')}px")
            if metadata.get("dpi"):
                tech_lines.append(f"- DPI: {metadata.get('dpi')}")
            if metadata.get("has_alpha") is not None:
                tech_lines.append(f"- Alpha Channel: {'Yes' if metadata.get('has_alpha') else 'No'}")
            if metadata.get("color_space"):
                tech_lines.append(f"- Color Space: {metadata.get('color_space')}")
            if metadata.get("extension"):
                tech_lines.append(f"- Format: {metadata.get('extension').upper()}")
            if metadata.get("file_size"):
                size_mb = metadata['file_size'] / (1024*1024)
                tech_lines.append(f"- File Size: {size_mb:.1f} MB")
            if metadata.get("pillow_color_analysis"):
                ca = metadata["pillow_color_analysis"]
                if ca.get("color_variance"):
                    tech_lines.append(f"- Color Variance: {ca['color_variance']}")
                if ca.get("dominant_tone"):
                    tech_lines.append(f"- Dominant Tone: {ca['dominant_tone']}")
                if ca.get("is_monochrome") is not None:
                    tech_lines.append(f"- Monochrome: {ca['is_monochrome']}")
                if ca.get("color_complexity"):
                    tech_lines.append(f"- Color Complexity: {ca['color_complexity']}")
            if metadata.get("pillow_background"):
                bg = metadata["pillow_background"]
                tech_lines.append(f"- Background Type (pixel analysis): {bg.get('type', 'unknown')}")
                if bg.get("transparent_percentage"):
                    tech_lines.append(f"- Transparent Area: {bg['transparent_percentage']}%")
            if metadata.get("pillow_composition"):
                comp = metadata["pillow_composition"]
                tech_lines.append(f"- Aspect Ratio: {comp.get('aspect_ratio', 'unknown')}")
                tech_lines.append(f"- Orientation: {comp.get('orientation', 'unknown')}")
            if metadata.get("pillow_artwork_type"):
                tech_lines.append(f"- Pillow Guess (artwork type): {metadata['pillow_artwork_type']}")
            if metadata.get("pillow_artistic_style"):
                tech_lines.append(f"- Pillow Guess (style): {metadata['pillow_artistic_style']}")
            tech_context = "\n".join(tech_lines)

        # Build the prompt
        prompt_parts = [
            "Analyze this artwork image in detail. Use the following technical pixel data to inform your analysis:",
            "",
            tech_context,
            "",
            "Based on both visual inspection AND the technical data above, return a JSON object with these exact fields:",
            "",
            '{"artwork_type": "one of: logo, illustration, character, text_design, typography, photo, sticker, cartoon, badge, crest, pattern, mixed",',
            '"artwork_type_confidence": 0.0 to 1.0,',
            '"subjects": [{"type": "primary or secondary", "label": "description", "confidence": 0.0 to 1.0}],',
            '"composition": {"layout": "centered, left_aligned, right_aligned, circular, symmetrical, asymmetrical", "orientation": "landscape, portrait, or square", "aspect_ratio_description": "description", "is_centered": true/false},',
            '"typography": {"has_text": true/false, "text_blocks": number, "decorative_text": true/false, "curved_text": true/false, "editable": true/false, "font_complexity": "simple, moderate, complex", "small_text_risk": true/false, "detected_text": "any readable text"},',
            '"background": {"type": "transparent, solid, gradient, complex, photo, pattern", "removable": true/false, "complexity": "none, low, medium, high", "description": "brief description"},',
            '"artistic_style": "one of: vintage, cartoon, realistic, watercolor, vector, sketch, comic, graffiti, minimal, modern, abstract, retro, hand_drawn",',
            '"style_confidence": 0.0 to 1.0,',
            '"color_analysis": {"dominant_colors": ["color1", "color2", "color3"], "color_complexity": "low, medium, high", "is_monochrome": true/false, "dominant_tone": "light, dark, warm, cool, neutral, vibrant"},',
            '"quality_notes": "brief assessment of image quality and production readiness"}',
            "",
            "Return ONLY the JSON object, no other text.",
        ]
        prompt = "\n".join(prompt_parts)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model="gpt-5.5",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=1500,
            )

            # Parse the response
            content = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)

            # Ensure all expected fields exist
            result.setdefault("artwork_type", "unknown")
            result.setdefault("artwork_type_confidence", 0.5)
            result.setdefault("subjects", [])
            result.setdefault("composition", {})
            result.setdefault("typography", {})
            result.setdefault("background", {})
            result.setdefault("artistic_style", "unknown")
            result.setdefault("style_confidence", 0.5)
            result.setdefault("color_analysis", {})
            result["engine"] = "gpt-5.5"

            return result

        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse GPT response as JSON: {str(e)}",
                "raw_response": content if 'content' in dir() else "",
                "artwork_type": "unknown",
                "artwork_type_confidence": 0.0,
                "subjects": [],
                "composition": {},
                "typography": {},
                "background": {},
                "artistic_style": "unknown",
                "style_confidence": 0.0,
                "color_analysis": {},
                "engine": "gpt-5.5",
            }
        except Exception as e:
            return {
                "error": f"GPT Vision API error: {str(e)}",
                "artwork_type": "unknown",
                "artwork_type_confidence": 0.0,
                "subjects": [],
                "composition": {},
                "typography": {},
                "background": {},
                "artistic_style": "unknown",
                "style_confidence": 0.0,
                "color_analysis": {},
                "engine": "gpt-5.5",
            }
