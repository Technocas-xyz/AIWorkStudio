"""File Inspection Engine - technical metadata extraction without visual reasoning."""

import io
import struct
from typing import Optional


class FileInspector:
    """Performs deep technical inspection of artwork files."""

    def inspect(self, file_bytes: bytes, filename: str, extension: str) -> dict:
        """Run complete file inspection. Returns structured metadata."""
        result = {
            "width": None,
            "height": None,
            "dpi": None,
            "resolution": None,
            "color_space": None,
            "bit_depth": None,
            "has_alpha": False,
            "has_transparency": False,
            "compression": None,
            "file_format": extension.upper(),
            "icc_profile": None,
            "exif_data": None,
            "is_corrupt": False,
            "issues": [],
        }

        if extension in ("png", "jpg", "jpeg", "webp", "tiff", "tif", "bmp"):
            result = self._inspect_raster(file_bytes, result)
        elif extension == "svg":
            result = self._inspect_svg(file_bytes, result)
        elif extension in ("psd", "psb"):
            result["file_format"] = "PSD" if extension == "psd" else "PSB"
            result["issues"].append("PSD inspection limited without psd-tools")
        elif extension == "pdf":
            result["file_format"] = "PDF"
            result["issues"].append("PDF inspection limited without pymupdf")

        # Calculate resolution string
        if result["width"] and result["height"]:
            result["resolution"] = f"{result['width']}x{result['height']}"

        return result

    def _inspect_raster(self, file_bytes: bytes, result: dict) -> dict:
        """Inspect raster image files using Pillow."""
        try:
            from PIL import Image, ExifTags

            img = Image.open(io.BytesIO(file_bytes))

            result["width"] = img.width
            result["height"] = img.height
            result["color_space"] = img.mode
            result["has_alpha"] = img.mode in ("RGBA", "LA", "PA")
            result["has_transparency"] = result["has_alpha"] or "transparency" in img.info
            result["compression"] = img.info.get("compression", "unknown")

            # DPI
            dpi = img.info.get("dpi")
            if dpi and isinstance(dpi, tuple):
                result["dpi"] = int(dpi[0])
            elif dpi:
                result["dpi"] = int(dpi)

            # Bit depth
            mode_bits = {"1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32, "CMYK": 32, "YCbCr": 24, "I": 32, "F": 32, "LA": 16}
            result["bit_depth"] = mode_bits.get(img.mode, 8)

            # ICC Profile
            icc = img.info.get("icc_profile")
            if icc:
                result["icc_profile"] = "embedded"
            else:
                result["icc_profile"] = "none"
                result["issues"].append("Missing color profile")

            # EXIF
            try:
                exif_data = img.getexif()
                if exif_data:
                    result["exif_data"] = {
                        ExifTags.TAGS.get(k, str(k)): str(v)
                        for k, v in exif_data.items()
                        if isinstance(v, (str, int, float))
                    }
            except Exception:
                pass

            # Validation checks
            if img.width < 50 or img.height < 50:
                result["issues"].append("Very low resolution - may not be suitable for production")
            if result["dpi"] and result["dpi"] < 72:
                result["issues"].append("DPI below minimum (72)")

            img.close()

        except Exception as e:
            result["is_corrupt"] = True
            result["issues"].append(f"File may be corrupt: {str(e)}")

        return result

    def _inspect_svg(self, file_bytes: bytes, result: dict) -> dict:
        """Inspect SVG vector files."""
        try:
            content = file_bytes.decode("utf-8", errors="ignore")
            result["color_space"] = "RGB"
            result["file_format"] = "SVG"
            result["compression"] = "none"
            result["bit_depth"] = None

            # Try to extract viewBox dimensions
            import re
            vb_match = re.search(r'viewBox="([^"]+)"', content)
            if vb_match:
                parts = vb_match.group(1).split()
                if len(parts) == 4:
                    result["width"] = int(float(parts[2]))
                    result["height"] = int(float(parts[3]))

            # Check for width/height attributes
            if not result["width"]:
                w_match = re.search(r'width="([\d.]+)', content)
                h_match = re.search(r'height="([\d.]+)', content)
                if w_match:
                    result["width"] = int(float(w_match.group(1)))
                if h_match:
                    result["height"] = int(float(h_match.group(1)))

            # Check for embedded scripts (security)
            if "<script" in content.lower():
                result["issues"].append("SVG contains embedded scripts - security risk")

        except Exception as e:
            result["issues"].append(f"SVG parsing error: {str(e)}")

        return result
