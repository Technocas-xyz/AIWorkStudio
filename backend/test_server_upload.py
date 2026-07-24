"""Test upload to remote server."""
import httpx

SERVER = "http://31.97.110.197:18080"

# Login
r = httpx.post(f'{SERVER}/api/auth/login', json={
    'email': 'admin@aiworkstudio.com',
    'password': 'Admin@123456',
    'remember_me': False
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create a tiny test image
from PIL import Image
import io
img = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)

# Upload
print("Uploading test image to server...")
r = httpx.post(f'{SERVER}/api/artworks/upload',
               headers=headers,
               files={'file': ('test_server.png', buf.getvalue(), 'image/png')},
               timeout=30)

print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
