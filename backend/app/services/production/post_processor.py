"""Image Post Processor - automated quality improvements after AI generation."""

import io
from typing import Optional


class PostProcessor:
    """Applies automated post-processing to generated images."""

    def process(self, image_bytes: bytes, generation_plan: dict) -> bytes:
        """Apply post-processing pipeline."""
        try:
            from PIL import Image, ImageFilter

            img = Image.open(io.BytesIO(image_bytes))

            # 1. Alpha cleanup (remove near-transparent pixels)
            if img.mode == "RGBA" and generation_plan.get("preserve_transparency", True):
                img = self._clean_alpha(img)

            # 2. Edge smoothing (slight anti-alias)
            if generation_plan.get("needs_edge_refinement"):
                img = self._smooth_edges(img)

            # 3. Canvas normalization (ensure even dimensions)
            img = self._normalize_canvas(img)

            # Save to bytes
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            img.close()
            return buf.getvalue()

        except Exception:
            # If post-processing fails, return original
            return image_bytes

    def _clean_alpha(self, img) -> 'Image':
        """Clean up alpha channel - remove near-transparent noise."""
        from PIL import Image
        if img.mode != "RGBA":
            return img

        r, g, b, a = img.split()
        # Threshold: pixels with alpha < 10 become fully transparent
        a = a.point(lambda x: 0 if x < 10 else x)
        # Pixels with alpha > 245 become fully opaque
        a = a.point(lambda x: 255 if x > 245 else x)
        return Image.merge("RGBA", (r, g, b, a))

    def _smooth_edges(self, img) -> 'Image':
        """Apply slight edge smoothing."""
        from PIL import ImageFilter
        if img.mode == "RGBA":
            # Only smooth the alpha channel edges
            r, g, b, a = img.split()
            # Very gentle smooth on alpha
            a = a.filter(ImageFilter.SMOOTH)
            from PIL import Image
            return Image.merge("RGBA", (r, g, b, a))
        return img

    def _normalize_canvas(self, img) -> 'Image':
        """Ensure dimensions are even numbers (required by some RIP software)."""
        w, h = img.size
        new_w = w if w % 2 == 0 else w + 1
        new_h = h if h % 2 == 0 else h + 1
        if new_w != w or new_h != h:
            from PIL import Image
            new_img = Image.new(img.mode, (new_w, new_h), (0, 0, 0, 0) if img.mode == "RGBA" else (255, 255, 255))
            new_img.paste(img, (0, 0))
            return new_img
        return img
