"""Centralized Aspect Ratio Service — used across the entire platform."""

import math
from typing import Optional, Tuple

# Standard aspect ratio classifications
STANDARD_RATIOS = {
    "1:1": "Square",
    "4:5": "Portrait Print",
    "5:4": "Landscape Print",
    "2:3": "Standard Photo",
    "3:2": "DSLR",
    "5:6": "Apparel Print",
    "6:5": "Landscape Apparel",
    "9:16": "Vertical Video",
    "16:9": "Widescreen",
    "3:4": "Portrait",
    "4:3": "Standard Display",
    "5:7": "DTF Standard",
    "7:5": "Wide DTF",
    "10:13": "DTF Front",
    "13:10": "Landscape DTF Front",
    "11:14": "Wide Front Print",
    "14:11": "Landscape Wide Print",
    "17:22": "Letter Portrait",
    "22:17": "Letter Landscape",
    "1:2": "Tall Narrow",
    "2:1": "Wide Banner",
}


def calculate_aspect_ratio(width: int, height: int) -> dict:
    """
    Calculate the simplified aspect ratio for given dimensions.
    Returns a structured dict with ratio, orientation, and classification.
    """
    if width <= 0 or height <= 0:
        return {
            "width": width,
            "height": height,
            "aspect_ratio": "0:0",
            "orientation": "unknown",
            "category": "Invalid",
        }

    # Calculate GCD and simplify
    gcd = math.gcd(width, height)
    ratio_w = width // gcd
    ratio_h = height // gcd

    # If the simplified numbers are too large (>50), approximate to nearest standard
    if ratio_w > 50 or ratio_h > 50:
        ratio_w, ratio_h = _approximate_ratio(width, height)

    aspect_ratio_str = f"{ratio_w}:{ratio_h}"

    # Orientation
    if width > height:
        orientation = "Landscape"
    elif height > width:
        orientation = "Portrait"
    else:
        orientation = "Square"

    # Classification
    category = STANDARD_RATIOS.get(aspect_ratio_str, "Custom")

    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio_str,
        "ratio_width": ratio_w,
        "ratio_height": ratio_h,
        "orientation": orientation,
        "category": category,
    }


def calculate_aspect_ratio_float(width: float, height: float) -> dict:
    """
    Calculate aspect ratio from floating-point dimensions (inches, mm).
    Normalizes to integers first by multiplying to remove decimals.
    """
    if width <= 0 or height <= 0:
        return calculate_aspect_ratio(0, 0)

    # Multiply both by enough to make them integers
    # Find the number of decimal places
    w_str = f"{width:.4f}".rstrip('0').rstrip('.')
    h_str = f"{height:.4f}".rstrip('0').rstrip('.')

    w_decimals = len(w_str.split('.')[1]) if '.' in w_str else 0
    h_decimals = len(h_str.split('.')[1]) if '.' in h_str else 0
    max_decimals = max(w_decimals, h_decimals)

    multiplier = 10 ** max_decimals
    int_w = int(round(width * multiplier))
    int_h = int(round(height * multiplier))

    return calculate_aspect_ratio(int_w, int_h)


def get_orientation(width: int, height: int) -> str:
    """Simple orientation check."""
    if width > height:
        return "Landscape"
    elif height > width:
        return "Portrait"
    return "Square"


def _approximate_ratio(width: int, height: int) -> Tuple[int, int]:
    """Approximate large ratios to the nearest standard ratio."""
    actual_ratio = width / height

    # Try matching against known ratios
    best_match = None
    best_diff = float('inf')

    known_ratios = [
        (1, 1), (4, 5), (5, 4), (2, 3), (3, 2), (5, 6), (6, 5),
        (9, 16), (16, 9), (3, 4), (4, 3), (5, 7), (7, 5),
        (10, 13), (13, 10), (11, 14), (14, 11), (1, 2), (2, 1),
        (17, 22), (22, 17),
    ]

    for rw, rh in known_ratios:
        diff = abs(actual_ratio - (rw / rh))
        if diff < best_diff:
            best_diff = diff
            best_match = (rw, rh)

    # Only use approximation if it's very close (within 5%)
    if best_match and best_diff < 0.05:
        return best_match

    # Otherwise reduce with a limit
    gcd = math.gcd(width, height)
    rw = width // gcd
    rh = height // gcd

    # Try scaling down large ratios
    for divisor in range(2, 20):
        if rw % divisor == 0 and rh % divisor == 0:
            rw //= divisor
            rh //= divisor

    # If still too large, use the closest approximation regardless
    if rw > 50 or rh > 50:
        if best_match:
            return best_match
        # Last resort: simplify by rounding
        if actual_ratio >= 1:
            return (round(actual_ratio * 10), 10)
        else:
            return (10, round(10 / actual_ratio))

    return (rw, rh)
