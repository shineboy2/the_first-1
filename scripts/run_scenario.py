import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123456"

def run():
    print("🚀 Starting Agency Scenario Execution...")
    
    # 1. Login
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Logged in.")

    # 2. Create Profile Type
    profile = {
        "name": "SalesAgent",
        "display_name": "Sales Agent",
        "description": "Can create booking orders",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/profile-types", json=profile, headers=headers)
    if resp.status_code in [200, 201]:
        print("✅ Profile Type 'SalesAgent' created.")
    elif resp.status_code == 400 and "exists" in resp.text:
        print("ℹ️ Profile Type 'SalesAgent' already exists.")
    else:
        print(f"⚠️ Profile Type creation issue: {resp.status_code} - {resp.text}")

    # 3. Create Request Type
    request_type = {
        "name": "Flight_Booking",
        "description": "Used by agents to issue flight tickets",
        "is_active": True
    }
    rt_id = None
    resp = requests.post(f"{BASE_URL}/request-types/", json=request_type, headers=headers)
    if resp.status_code == 201:
        rt_id = resp.json()["id"]
        print(f"✅ Request Type 'Flight_Booking' created (ID: {rt_id}).")
    else:
        # Try to find it
        resp = requests.get(f"{BASE_URL}/request-types/", headers=headers)
        for rt in resp.json():
            if rt["name"] == "Flight_Booking":
                rt_id = rt["id"]
                print(f"ℹ️ Request Type 'Flight_Booking' already exists (ID: {rt_id}).")
                break

    if not rt_id:
        print("❌ Could not get Request Type ID.")
        return

    # 4. Configure Parameters
    params_config = {
        "name": "Flight_Booking",
        "available_indices": ["flight_data"],
        "parameters": [
            {"name": "Passenger_Name", "parameter_type": "string", "is_required": True, "placeholder_key": "passenger_name"},
            {"name": "Flight_Number", "parameter_type": "string", "is_required": True, "placeholder_key": "flight_no"},
            {"name": "PNR", "parameter_type": "string", "is_required": True, "placeholder_key": "pnr_code"}
        ]
    }
    resp = requests.put(f"{BASE_URL}/request-types/{rt_id}/configure", json=params_config, headers=headers)
    if resp.status_code == 200:
        print("✅ Parameters configured.")
    else:
        print(f"❌ Parameter config failed: {resp.text}")

    # 5. Configure ES Template
    query_config = {
        "elasticsearch_query_template": {
            "query": {
                "bool": {
                    "must": [
                        { "match": { "flight_no": "{{flight_no}}" } },
                        { "match": { "pnr": "{{pnr_code}}" } }
                    ]
                }
            }
        }
    }
    resp = requests.put(f"{BASE_URL}/request-types/{rt_id}/query", json=query_config, headers=headers)
    if resp.status_code == 200:
        print("✅ ES Query Template configured.")
    else:
        print(f"❌ Query config failed: {resp.text}")

    # 6. Grant Profile Access
    access = {
        "profile_type_ids": ["SalesAgent"],
        "max_requests_per_day": 100,
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/request-types/{rt_id}/profile-access", json=access, headers=headers)
    if resp.status_code in [200, 201]:
        print("✅ Access granted to SalesAgent.")
    else:
        print(f"❌ Granting access failed: {resp.text}")

    # 7. Create User
    user = {
        "username": "agent001",
        "password": "agentPassword123!",
        "full_name": "Agency Sales Agent 01",
        "profile_type": "SalesAgent",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/users", json=user, headers=headers)
    if resp.status_code in [200, 201]:
        print("✅ User 'agent001' created.")
    elif resp.status_code in [400, 409]:
        print("ℹ️ User 'agent001' already exists.")
    else:
        print(f"❌ User creation failed: {resp.text}")

    print("\n🏁 Agency Scenario Setup Completed successfully.")

if __name__ == "__main__":
    run()
