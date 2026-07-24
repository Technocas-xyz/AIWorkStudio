"""Preview generation service for artwork thumbnails."""

import io
import os
import uuid
from typing import Optional

PREVIEW_SIZES = {
    "thumbnail": (200, 200),
    "medium": (600, 600),
    "large": (1200, 1200),
}


def generate_previews(image_bytes: bytes, artwork_id: str) -> dict:
    """Generate thumbnail, medium, and large previews. Returns dict of preview_type -> bytes."""
    try:
        from PIL import Image
    except ImportError:
        return {}

    previews = {}
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGBA for transparency support
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        for preview_type, max_size in PREVIEW_SIZES.items():
            preview_img = img.copy()
            preview_img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Create checkerboard background for transparent images
            if preview_img.mode == "RGBA":
                bg = _create_checkerboard(preview_img.width, preview_img.height)
                bg.paste(preview_img, mask=preview_img.split()[3])
                preview_img = bg

            buf = io.BytesIO()
            preview_img.save(buf, format="PNG", optimize=True)
            previews[preview_type] = {
                "bytes": buf.getvalue(),
                "width": preview_img.width,
                "height": preview_img.height,
            }

        img.close()
    except Exception:
        pass

    return previews


def _create_checkerboard(width: int, height: int, square_size: int = 10):
    """Create a checkerboard background for transparent images."""
    from PIL import Image

    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if (x // square_size + y // square_size) % 2 == 0:
                pixels[x, y] = (255, 255, 255)
            else:
                pixels[x, y] = (204, 204, 204)
    return img
