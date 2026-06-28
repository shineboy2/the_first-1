import requests

# Login Request Network
req = requests.post("http://localhost:8001/api/v1/auth/login", data={
    "username": "admin",
    "password": "123456",
    "captcha_id": "11111111-1111-1111-1111-111111111111",
    "captcha_solution": "12345"
})
req_token = req.json()["access_token"]
req_headers = {"Authorization": f"Bearer {req_token}", "Content-Type": "application/json"}

print("Fetching request types...")
req_types = requests.get("http://localhost:8001/api/v1/request-types/", headers=req_headers)
if req_types.status_code == 200:
    print(req_types.json())
else:
    print("Error:", req_types.json())
