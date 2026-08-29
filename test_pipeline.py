import time
import requests

# 1. Get Token
auth_res = requests.post("http://localhost:8001/api/v1/auth/token", data={"username": "admin", "password": "Admin@1234"})
token = auth_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get Request Types
types_res = requests.get("http://localhost:8001/api/v1/request-types/", headers=headers)
types = types_res.json()
if not types:
    print("No request types available")
    exit(1)
req_type_id = "get_external_users"
print(f"Using request type: {req_type_id}")

# 3. Create Request
payload = {
    "name": f"Test Request {time.time()}",
    "request": {
        "serviceName": req_type_id,
        "fieldRequest": {"some_param": "value"}
    }
}
req_res = requests.post("http://localhost:8001/api/v1/requests/", headers=headers, json=payload)
req_id = req_res.json()["id"]
print(f"Created request: {req_id}")

# 4. Wait for completion
for _ in range(30):
    status_res = requests.get(f"http://localhost:8001/api/v1/requests/{req_id}/status", headers=headers)
    if status_res.status_code == 429:
        print("Rate limited, sleeping for 10s...")
        time.sleep(10)
        continue
    
    status_data = status_res.json()
    status = status_data.get("status")
    if not status:
        print(f"Unexpected response: {status_data}")
        break
        
    print(f"Status: {status}")
    if status == "completed":
        print("Pipeline test successful!")
        exit(0)
    elif status == "failed":
        print(f"Pipeline test failed! Error: {status_data.get('error_message')}")
        exit(1)
    time.sleep(6)

print("Pipeline test timed out!")
exit(1)
