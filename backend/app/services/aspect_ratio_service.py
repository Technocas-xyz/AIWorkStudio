"""Centralized Aspect Ratio Service â€” used across the entire platform."""

import math
from typing import Optional, Tuple

# Standard aspect ratio classifications (for reference)
STANDARD_RATIOS = {
    "1:1": "Square",
    "1:1.25": "Portrait Print (4:5)",
    "1:1.5": "Standard Photo (2:3)",
    "1:1.33": "Portrait (3:4)",
    "1:1.78": "Vertical Video (9:16)",
    "1:2": "Tall Narrow",
    "1:1.4": "DTF Standard (5:7)",
    "1:1.2": "Apparel Print (5:6)",
}


def calculate_aspect_ratio(width: int, height: int) -> dict:
    """
    Calculate the aspect ratio normalized to width=1.
    Format: 1:X where X = height/width (rounded to 2 decimals).
    """
    if width <= 0 or height <= 0:
        return {
            "width": width,
            "height": height,
            "aspect_ratio": "0:0",
            "orientation": "unknown",
            "category": "Invalid",
        }

    # Normalize: width = 1, height = height/width
    ratio_value = round(height / width, 2)

    # Display format
    if ratio_value == 1.0:
        aspect_ratio_str = "1:1"
    else:
        # Remove trailing zeros: 1.50 -> 1.5, 2.00 -> 2
        ratio_display = f"{ratio_value:.2f}".rstrip('0').rstrip('.')
        aspect_ratio_str = f"1:{ratio_display}"

    # Orientation
    if width > height:
        orientation = "Landscape"
    elif height > width:
        orientation = "Portrait"
    else:
        orientation = "Square"

    # Classification based on ratio value
    category = _classify_ratio(ratio_value)

    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio_str,
        "ratio_value": ratio_value,
        "orientation": orientation,
        "category": category,
    }


def _classify_ratio(ratio_value: float) -> str:
    """Classify the ratio value to a production category."""
    # Map common ratio values to categories
    classifications = [
        (1.0, "Square"),
        (1.25, "Portrait Print (4:5)"),
        (0.8, "Landscape Print (5:4)"),
        (1.5, "Standard Photo (2:3)"),
        (0.67, "DSLR Landscape (3:2)"),
        (1.2, "Apparel Print (5:6)"),
        (0.83, "Landscape Apparel (6:5)"),
        (1.78, "Vertical Video (9:16)"),
        (0.56, "Widescreen (16:9)"),
        (1.33, "Portrait (3:4)"),
        (0.75, "Standard Display (4:3)"),
        (1.4, "DTF Standard (5:7)"),
        (0.71, "Wide DTF (7:5)"),
        (2.0, "Tall Narrow (1:2)"),
        (0.5, "Wide Banner (2:1)"),
    ]

    # Find closest match (within 5% tolerance)
    best_match = "Custom"
    best_diff = 0.05

    for target_ratio, name in classifications:
        diff = abs(ratio_value - target_ratio)
        if diff < best_diff:
            best_diff = diff
            best_match = name

    return best_match


def calculate_aspect_ratio_float(width: float, height: float) -> dict:
    """
    Calculate aspect ratio from floating-point dimensions (inches, mm).
    """
    if width <= 0 or height <= 0:
        return calculate_aspect_ratio(0, 0)
    return calculate_aspect_ratio(int(round(width * 100)), int(round(height * 100)))


def get_orientation(width: int, height: int) -> str:
    """Simple orientation check."""
    if width > height:
        return "Landscape"
    elif height > width:
        return "Portrait"
    return "Square"


