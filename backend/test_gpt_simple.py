"""Test GPT-5.5 vs Pillow - output to file."""
import httpx, json

r = httpx.post('http://localhost:8000/api/auth/login', json={
    'email': 'admin@aiworkstudio.com', 'password': 'Admin@123456', 'remember_me': False
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

artworks = httpx.get('http://localhost:8000/api/artworks', headers=headers).json()['data']['items']
art = artworks[0]

# GPT
r1 = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
                json={'artwork_id': art['id'], 'engine': 'gpt'}, timeout=60)
gpt_job = r1.json()['data']
gpt_report = httpx.get(f"http://localhost:8000/api/analysis/{gpt_job['job_id']}/report", headers=headers).json()['data']

# Pillow
r2 = httpx.post('http://localhost:8000/api/analysis/start', headers=headers,
                json={'artwork_id': art['id'], 'engine': 'pillow'}, timeout=30)
pil_job = r2.json()['data']
pil_report = httpx.get(f"http://localhost:8000/api/analysis/{pil_job['job_id']}/report", headers=headers).json()['data']

output = []
output.append(f"Artwork: {art['original_filename']} ({art['width']}x{art['height']})")
output.append(f"")
output.append(f"=== GPT-5.5 (duration: {gpt_job.get('duration_seconds', 0):.2f}s) ===")
gva = gpt_report['visual_analysis']
output.append(f"Engine: {gva.get('engine_used')}")
output.append(f"Type: {gva.get('artwork_type')} ({gva.get('artwork_type_confidence')})")
output.append(f"Style: {gva.get('artistic_style')}")
output.append(f"BG: {gva.get('background', {}).get('type')}")
output.append(f"Typography: {gva.get('typography', {})}")
output.append(f"Colors: {gva.get('color_analysis', {})}")
output.append(f"Score: {gpt_report['overall_score']}")
if gva.get('error'):
    output.append(f"ERROR: {gva['error']}")
if gva.get('quality_notes'):
    output.append(f"Quality: {gva['quality_notes']}")
output.append(f"")
output.append(f"=== PILLOW (duration: {pil_job.get('duration_seconds', 0):.2f}s) ===")
pva = pil_report['visual_analysis']
output.append(f"Engine: {pva.get('engine_used')}")
output.append(f"Type: {pva.get('artwork_type')} ({pva.get('artwork_type_confidence')})")
output.append(f"Style: {pva.get('artistic_style')}")
output.append(f"BG: {pva.get('background', {}).get('type')}")
output.append(f"Score: {pil_report['overall_score']}")

result = "\n".join(output)
with open("test_result.txt", "w") as f:
    f.write(result)
print(result)
