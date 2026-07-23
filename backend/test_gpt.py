"""Test GPT-5.5 Vision analysis engine."""
import httpx, json

r = httpx.post('http://localhost:8000/api/auth/login', json={
    'email': 'admin@aiworkstudio.com', 'password': 'Admin@123456', 'remember_me': False
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get first artwork
artworks = httpx.get('http://localhost:8000/api/artworks', headers=headers).json()['data']['items']
art = artworks[0]
print(f"Artwork: {art['original_filename']} ({art['width']}x{art['height']})")
print()

# Run GPT analysis
print("Running GPT-5.5 analysis...")
r = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
               json={'artwork_id': art['id'], 'engine': 'gpt'}, timeout=60)
job = r.json()['data']
print(f"Status: {job['status']}")
print(f"Duration: {job.get('duration_seconds', 'N/A')}s")
print()

if job['status'] != 'completed':
    print(f"ERROR: {job.get('error')}")
    exit(1)

# Get report
report = httpx.get(f"http://localhost:8000/api/analysis/{job['job_id']}/report", headers=headers).json()['data']
va = report['visual_analysis']

print("=== GPT-5.5 VISUAL ANALYSIS ===")
print(f"Engine Used: {va.get('engine_used', 'unknown')}")
print(f"Artwork Type: {va.get('artwork_type')} ({va.get('artwork_type_confidence', 0):.0%})")
print(f"Artistic Style: {va.get('artistic_style')} ({va.get('style_confidence', 0):.0%})")
print(f"Background: {va.get('background', {}).get('type')} (removable: {va.get('background', {}).get('removable')})")
print()

typo = va.get('typography', {})
print(f"Typography: has_text={typo.get('has_text')} blocks={typo.get('text_blocks')} curved={typo.get('curved_text')}")
if typo.get('detected_text'):
    print(f"  Detected text: \"{typo['detected_text']}\"")
print()

colors = va.get('color_analysis', {})
print(f"Colors: complexity={colors.get('color_complexity')} tone={colors.get('dominant_tone')}")
if colors.get('dominant_colors'):
    print(f"  Dominant: {', '.join(colors['dominant_colors'][:5])}")
print()

comp = va.get('composition', {})
print(f"Composition: layout={comp.get('layout')} centered={comp.get('is_centered')}")
print()

if va.get('quality_notes'):
    print(f"Quality Notes: {va['quality_notes']}")
    print()

if va.get('error'):
    print(f"⚠️ GPT Error: {va['error']}")
else:
    print("✓ GPT-5.5 Vision analysis completed successfully!")

# Compare with Pillow
print("\n--- Running Pillow for comparison ---")
r2 = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
                json={'artwork_id': art['id'], 'engine': 'pillow'}, timeout=30)
job2 = r2.json()['data']
if job2['status'] == 'completed':
    report2 = httpx.get(f"http://localhost:8000/api/analysis/{job2['job_id']}/report", headers=headers).json()['data']
    va2 = report2['visual_analysis']
    print(f"Pillow Type: {va2.get('artwork_type')} | GPT Type: {va.get('artwork_type')}")
    print(f"Pillow Style: {va2.get('artistic_style')} | GPT Style: {va.get('artistic_style')}")
    print(f"Pillow BG: {va2.get('background', {}).get('type')} | GPT BG: {va.get('background', {}).get('type')}")
    print(f"Pillow Score: {report2['overall_score']} | GPT Score: {report['overall_score']}")
