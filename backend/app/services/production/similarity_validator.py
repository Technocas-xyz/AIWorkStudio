"""Similarity Validator - compares generated artwork with original."""

import io
import math
from typing import Optional


class SimilarityValidator:
    """Validates that generated artwork matches original intent."""

    def compare(self, original_bytes: bytes, generated_bytes: bytes) -> float:
        """Compare original and generated images. Returns similarity 0.0-1.0."""
        try:
            from PIL import Image, ImageStat

            orig = Image.open(io.BytesIO(original_bytes)).convert("RGB")
            gen = Image.open(io.BytesIO(generated_bytes)).convert("RGB")

            # Resize both to same size for comparison
            compare_size = (256, 256)
            orig_resized = orig.resize(compare_size, Image.Resampling.LANCZOS)
            gen_resized = gen.resize(compare_size, Image.Resampling.LANCZOS)

            # Pixel-level comparison (MSE)
            mse = self._calculate_mse(orig_resized, gen_resized)
            pixel_similarity = max(0, 1 - (mse / 10000))

            # Color histogram comparison
            color_similarity = self._compare_histograms(orig_resized, gen_resized)

            # Structural similarity (simplified)
            structural_similarity = self._structural_compare(orig_resized, gen_resized)

            # Weighted average
            overall = (pixel_similarity * 0.3 + color_similarity * 0.4 + structural_similarity * 0.3)

            orig.close()
            gen.close()

            return min(1.0, max(0.0, overall))

        except Exception:
            return 0.5  # Default if comparison fails

    def assess_quality(self, image_bytes: bytes) -> float:
        """Assess the quality of a generated image. Returns 0.0-1.0."""
        try:
            from PIL import Image, ImageStat, ImageFilter

            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != "RGB":
                rgb = img.convert("RGB")
            else:
                rgb = img

            gray = rgb.convert("L")

            # Sharpness (Laplacian variance)
            laplacian = gray.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
            lap_stat = ImageStat.Stat(laplacian)
            sharpness = min(1.0, lap_stat.var[0] / 2000)

            # Dynamic range
            gray_stat = ImageStat.Stat(gray)
            dyn_range = (gray_stat.extrema[0][1] - gray_stat.extrema[0][0]) / 255

            # No pure black/white clipping
            histogram = gray.histogram()
            total = sum(histogram)
            clip_pct = (histogram[0] + histogram[255]) / total if total > 0 else 0
            no_clipping = max(0, 1 - clip_pct * 5)

            # Overall quality
            quality = (sharpness * 0.4 + dyn_range * 0.3 + no_clipping * 0.3)

            img.close()
            return min(1.0, max(0.0, quality))

        except Exception:
            return 0.5

    def _calculate_mse(self, img1, img2) -> float:
        """Calculate Mean Squared Error between two images."""
        from PIL import ImageChops, ImageStat
        diff = ImageChops.difference(img1, img2)
        stat = ImageStat.Stat(diff)
        mse = sum(s * s for s in stat.mean) / len(stat.mean)
        return mse

    def _compare_histograms(self, img1, img2) -> float:
        """Compare color histograms of two images."""
        h1 = img1.histogram()
        h2 = img2.histogram()
        # Normalized histogram intersection
        min_sum = sum(min(a, b) for a, b in zip(h1, h2))
        max_sum = max(sum(h1), sum(h2))
        return min_sum / max_sum if max_sum > 0 else 0

    def _structural_compare(self, img1, img2) -> float:
        """Simplified structural similarity."""
        from PIL import ImageStat
        stat1 = ImageStat.Stat(img1)
        stat2 = ImageStat.Stat(img2)

        # Compare means and variances
        mean_diff = sum(abs(a - b) for a, b in zip(stat1.mean, stat2.mean)) / (3 * 255)
        var_diff = sum(abs(a - b) for a, b in zip(stat1.var, stat2.var)) / (3 * 65025)

        similarity = 1 - (mean_diff * 0.5 + var_diff * 0.5)
        return max(0, min(1, similarity))
