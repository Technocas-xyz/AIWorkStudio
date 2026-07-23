"""Test aspect ratio service."""
import os
os.environ['APP_ENV'] = 'local'
from app.services.aspect_ratio_service import calculate_aspect_ratio

tests = [
    (10, 10), (20, 20), (12, 18), (18, 12), (24, 36),
    (4500, 5400), (1080, 1350), (1080, 1920), (1920, 1080),
    (1239, 1652), (1664, 2224), (1382, 1843), (1546, 1707),
    (6000, 4000), (30, 20), (928, 1152),
]

print(f"{'Dimensions':<16} {'Ratio':<8} {'Category':<20} {'Orientation'}")
print("-" * 65)
for w, h in tests:
    r = calculate_aspect_ratio(w, h)
    print(f"{w}×{h:<12} {r['aspect_ratio']:<8} {r['category']:<20} {r['orientation']}")
