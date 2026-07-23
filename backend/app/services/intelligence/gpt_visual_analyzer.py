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

        # Build the prompt
        prompt = """Analyze this artwork image in detail. Return a JSON object with these exact fields:

{
  "artwork_type": "one of: logo, illustration, character, text_design, typography, photo, sticker, cartoon, badge, crest, pattern, mixed",
  "artwork_type_confidence": 0.0 to 1.0,
  "subjects": [{"type": "primary or secondary", "label": "description", "confidence": 0.0 to 1.0}],
  "composition": {
    "layout": "centered, left_aligned, right_aligned, circular, symmetrical, asymmetrical",
    "orientation": "landscape, portrait, or square",
    "aspect_ratio_description": "description",
    "is_centered": true/false
  },
  "typography": {
    "has_text": true/false,
    "text_blocks": number,
    "decorative_text": true/false,
    "curved_text": true/false,
    "editable": true/false,
    "font_complexity": "simple, moderate, complex",
    "small_text_risk": true/false,
    "detected_text": "any readable text"
  },
  "background": {
    "type": "transparent, solid, gradient, complex, photo, pattern",
    "removable": true/false,
    "complexity": "none, low, medium, high",
    "description": "brief description"
  },
  "artistic_style": "one of: vintage, cartoon, realistic, watercolor, vector, sketch, comic, graffiti, minimal, modern, abstract, retro, hand_drawn",
  "style_confidence": 0.0 to 1.0,
  "color_analysis": {
    "dominant_colors": ["color1", "color2", "color3"],
    "color_complexity": "low, medium, high",
    "is_monochrome": true/false,
    "dominant_tone": "light, dark, warm, cool, neutral, vibrant"
  },
  "quality_notes": "brief assessment of image quality and production readiness"
}

Return ONLY the JSON object, no other text."""

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
