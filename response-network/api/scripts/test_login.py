import requests
import json

print("Testing login endpoint...")
print("=" * 60)

url = 'http://localhost:8001/api/v1/auth/login'
data = {'username': 'admin', 'password': 'admin123'}

print(f"URL: {url}")
print(f"Data: {data}")
print()

try:
    r = requests.post(url, data=data)
    print(f'Status Code: {r.status_code}')
    print(f'Headers: {dict(r.headers)}')
    print()
    print(f'Response Text: {r.text}')
    print()
    
    if r.status_code == 200:
        try:
            json_data = r.json()
            print(f'JSON Response: {json.dumps(json_data, indent=2)}')
        except:
            print("Could not parse JSON")
except Exception as e:
    print(f'Error: {e}')
