"""Quick test of aspect ratio analysis."""
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

# Run analysis
r = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
               json={'artwork_id': art['id'], 'engine': 'pillow'}, timeout=30)
job = r.json()['data']
print(f"Status: {job['status']}")

# Get report
report = httpx.get(f"http://localhost:8000/api/analysis/{job['job_id']}/report", headers=headers).json()['data']
ar = report['geometry_analysis'].get('aspect_ratio')

if ar:
    print(f"\n📐 ASPECT RATIO ANALYSIS")
    print(f"Current: {ar['current_ratio_display']} ({ar['current_ratio']}) - {ar['current_orientation']}")
    print(f"Summary: {ar['summary']}")
    print(f"\nTop Recommendations:")
    for rec in ar['recommendations'][:6]:
        print(f"  {rec['score']:3d} | {rec['status']:15s} | {rec['name']:20s} | Crop: {rec['crop_loss_pct']:5.1f}% | Expand: {rec['canvas_expand_pct']:5.1f}% | {rec['method']}")
        if rec['risks']:
            for risk in rec['risks']:
                print(f"      ⚠️  {risk}")
    print(f"\n✓ Aspect ratio analysis working!")
else:
    print("ERROR: No aspect ratio data in report")
