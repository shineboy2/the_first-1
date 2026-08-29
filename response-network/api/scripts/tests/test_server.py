import requests

print("Testing basic server connectivity...")
print("=" * 60)

docs_url = 'http://localhost:8001/docs'
print(f"Testing: {docs_url}")
try:
    r = requests.get(docs_url)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("[OK] Server is running!")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print()
health_url = 'http://localhost:8001/api/v1/system/health'
print(f"Testing: {health_url}")
try:
    r = requests.get(health_url)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print()
print("Now testing login...")
print("=" * 60)
login_url = 'http://localhost:8001/api/v1/auth/login'
print(f"URL: {login_url}")

r = requests.post(login_url, data={'username': 'admin', 'password': 'admin123'})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
