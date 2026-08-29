import urllib.request
import urllib.error
import urllib.parse
import json
import time
import sys
import uuid
import os

REQ_BASE = "http://localhost:8001/api/v1"

def login():
    data = urllib.parse.urlencode({
        "username": "admin",
        "password": "Admin@1234"
    }).encode("utf-8")
    req = urllib.request.Request(f"{REQ_BASE}/auth/token", data=data)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise Exception(f"Login failed: {e.code} {e.read().decode('utf-8')}")

def fetch_request_types(token):
    req = urllib.request.Request(f"{REQ_BASE}/request-types/", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        types = json.loads(res.read())
        print("Request types response:", json.dumps(types, indent=2))
        return types

def fetch_json(url, token, data=None):
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read()), res.status

def main():
    print("Logging in...")
    try:
        token = login()
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)

    print("Fetching request types...")
    types, _ = fetch_json(f"{REQ_BASE}/request-types/", token)
    if not types:
        print("No request types available! Baseline cannot proceed.")
        sys.exit(1)
    
    req_type = types[0]
    service_name = req_type["name"]
    print(f"Using request type: {service_name}")
    
    req_name = f"E2E_Test_{uuid.uuid4().hex[:8]}"

    payload = {
        "reqState": "PENDING",
        "name": req_name,
        "request": {
            "serviceName": service_name,
            "fieldRequest": {
                "query_params": {
                    "sample": "test_data"
                }
            }
        }
    }

    print(f"Submitting request {req_name}...")
    try:
        req_data, status = fetch_json(f"{REQ_BASE}/requests/", token, data=payload)
    except urllib.error.HTTPError as e:
        print(f"Failed to create request: {e.code} {e.read().decode('utf-8')}")
        sys.exit(1)

    req_id = req_data["id"]
    print(f"Request created with ID: {req_id}. Status: {req_data['status']}")

    print("Polling for completion...")
    max_wait = 120 # 2 minutes max
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            status_data, _ = fetch_json(f"{REQ_BASE}/requests/{req_id}/status", token)
        except Exception as e:
            print(f"Error fetching status: {e}")
            time.sleep(5)
            continue

        current_status = status_data["status"]
        print(f"Current Status: {current_status}")
        
        if current_status.lower() == "completed":
            print(f"Request completed in {time.time() - start:.1f}s!")
            
            try:
                resp_data, _ = fetch_json(f"{REQ_BASE}/requests/{req_id}/response", token)
                print("Response fetched successfully:")
                print(json.dumps(resp_data, indent=2))
                print("--- BASELINE E2E SUCCESS ---")
                sys.exit(0)
            except urllib.error.HTTPError as e:
                print(f"Failed to fetch response details: {e.code} {e.read().decode('utf-8')}")
                sys.exit(1)
                
        elif current_status.lower() == "failed":
            print(f"Request FAILED in {time.time() - start:.1f}s!")
            sys.exit(1)
            
        time.sleep(2)
    
    print("Timeout reached while waiting for request to complete.")
    sys.exit(1)

if __name__ == "__main__":
    main()
