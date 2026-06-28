import requests
import json
import time
import os

# Connect to Redis to set captcha
os.system("docker exec sim-req-redis redis-cli -a 'redis_secure_pass' SETEX captcha:11111111-1111-1111-1111-111111111111 300 12345 > /dev/null 2>&1")

# Login Request Network
req = requests.post("http://localhost:8001/api/v1/auth/login", data={
    "username": "admin",
    "password": "123456",
    "captcha_id": "11111111-1111-1111-1111-111111111111",
    "captcha_solution": "12345"
})
req.raise_for_status()
req_token = req.json()["access_token"]
req_headers = {"Authorization": f"Bearer {req_token}", "Content-Type": "application/json"}

print("Triggering import in Request Network...")
import_req = requests.post("http://localhost:8001/api/v1/admin/imports/test/request_types_import", headers=req_headers)
if import_req.status_code != 200:
    print(import_req.json())
else:
    print("Import triggered:", import_req.json())
