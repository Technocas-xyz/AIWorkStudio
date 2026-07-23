"""Test the Artwork Intelligence Engine end-to-end."""
import httpx
import json

# Login
r = httpx.post('http://localhost:8000/api/auth/login', json={
    'email': 'admin@aiworkstudio.com',
    'password': 'Admin@123456',
    'remember_me': False
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get first artwork
r = httpx.get('http://localhost:8000/api/artworks', headers=headers)
artworks = r.json()['data']['items']
if not artworks:
    print("No artworks found! Upload one first.")
    exit(1)

artwork = artworks[0]
print(f"Analyzing: {artwork['original_filename']} ({artwork['width']}x{artwork['height']}) [{artwork['extension']}]")
print(f"  ID: {artwork['id']}")
print()

# Start analysis
r = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
               json={'artwork_id': artwork['id']}, timeout=30)
result = r.json()
print(f"Analysis Status: {result['data']['status']}")
print(f"  Duration: {result['data'].get('duration_seconds', 'N/A')}s")
print()

if result['data']['status'] != 'completed':
    print(f"ERROR: {result['data'].get('error')}")
    exit(1)

# Get full report
job_id = result['data']['job_id']
r = httpx.get(f'http://localhost:8000/api/analysis/{job_id}/report', headers=headers)
report = r.json()['data']

print(f"=== ANALYSIS REPORT ===")
print(f"Overall Score: {report['overall_score']}/100")
print(f"Risk Level: {report['risk_level']}")
print()

print("--- File Inspection ---")
fi = report['file_inspection']
print(f"  Format: {fi['file_format']} | Color: {fi['color_space']} | DPI: {fi['dpi']}")
print(f"  Alpha: {fi['has_alpha']} | Corrupt: {fi['is_corrupt']}")
print()

print("--- Visual Analysis ---")
va = report['visual_analysis']
print(f"  Type: {va['artwork_type']} ({va['artwork_type_confidence']:.0%})")
print(f"  Style: {va['artistic_style']} | Background: {va['background']['type']}")
print()

print("--- Geometry ---")
ga = report['geometry_analysis']
print(f"  Coverage: {ga['subject_coverage_pct']}% | Empty: {ga['empty_space_pct']}%")
print(f"  Centered: {ga['subject_centered']} | Edge Contact: {any(ga['edge_contact'].values())}")
print()

print("--- Production ---")
pa = report['production_analysis']
print(f"  Safe Print: {pa['safe_print_width_inches']}\" x {pa['safe_print_height_inches']}\"")
print(f"  Difficulty: {pa['production_difficulty']} | Score: {pa['production_score']}")
print()

print("--- Risks ---")
ra = report['risk_assessment']
print(f"  Level: {ra['risk_level']} | Count: {ra['risk_count']}")
for risk in ra['risks']:
    print(f"  [{risk['severity'].upper()}] {risk['title']}: {risk['description']}")
print()

print("--- Generation Plan ---")
gp = report['generation_plan']
print(f"  Model: {gp['recommended_model']}")
print(f"  Needs BG Removal: {gp['needs_background_removal']}")
print(f"  Needs Super Res: {gp['needs_super_resolution']}")
print(f"  Needs Reconstruction: {gp['needs_reconstruction']}")
print(f"  Product: {gp['recommended_product']}")
print(f"  Score: {gp['overall_score']}/100")
print()
print("✓ Analysis Engine working correctly!")
