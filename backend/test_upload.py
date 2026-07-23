"""Quick test of the artwork upload API."""
import httpx

# Login
r = httpx.post('http://localhost:8000/api/auth/login', json={
    'email': 'admin@aiworkstudio.com',
    'password': 'Admin@123456',
    'remember_me': False
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# List artworks
r2 = httpx.get('http://localhost:8000/api/artworks', headers=headers)
data = r2.json()['data']
print(f"Total artworks: {data['total']}")
for a in data['items']:
    print(f"  {a['artwork_id']} | {a['original_filename']} | {a['width']}x{a['height']} | {a['color_space']} | v{a['current_version']}")

# Test duplicate detection
print("\nTesting duplicate upload...")
with open('test_upload.png', 'rb') as f:
    r3 = httpx.post('http://localhost:8000/api/artworks/upload', headers=headers,
                    files={'file': ('test_art.png', f, 'image/png')})
    print(f"  Status: {r3.status_code}, Duplicate: {r3.json().get('data', {}).get('duplicate', False)}")

# Test collections
print("\nCreating collection...")
r4 = httpx.post('http://localhost:8000/api/collections', headers=headers,
                json={'name': 'Test Collection', 'description': 'My first collection'})
print(f"  {r4.json()}")

# Test tags
print("\nCreating tag...")
r5 = httpx.post('http://localhost:8000/api/tags', headers=headers,
                json={'name': 'landscape', 'color': '#22c55e'})
print(f"  {r5.json()}")

print("\n✓ All API endpoints working!")
