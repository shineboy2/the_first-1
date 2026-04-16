import requests
import json
import sys

# Configuration
BASE_URL = "http://192.168.214.141:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_secure_password_change_me" # This will be updated to admin123456 after deployment

def setup_scenario():
    print("🚀 Starting Airline Agency Scenario Setup...")
    
    # 1. Login
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in as admin.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    # 2. Create Profile Types (Roles)
    roles = [
        {"name": "Sales_Agent", "description": "Can create booking orders", "is_active": True},
        {"name": "Agency_Manager", "description": "Can view reports and manage office", "is_active": True}
    ]
    
    for role in roles:
        try:
            resp = requests.post(f"{BASE_URL}/profile-types", json=role, headers=headers)
            if resp.status_code == 201:
                print(f"✅ Created role: {role['name']}")
            elif resp.status_code == 409:
                print(f"ℹ️ Role {role['name']} already exists.")
            else:
                resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ Failed to create role {role['name']}: {e}")

    # 3. Create Request Type
    request_type = {
        "name": "Flight_Booking_Order",
        "description": "Used by agents to issue flight tickets",
        "is_active": True
    }
    
    rt_id = None
    try:
        resp = requests.post(f"{BASE_URL}/request-types/", json=request_type, headers=headers)
        if resp.status_code == 201:
            rt_id = resp.json()["id"]
            print(f"✅ Created request type: {request_type['name']} (ID: {rt_id})")
        elif resp.status_code == 400: # Already exists?
            # Find existing ID
            list_resp = requests.get(f"{BASE_URL}/request-types/", headers=headers)
            list_resp.raise_for_status()
            for item in list_resp.json():
                if item["name"] == request_type["name"]:
                    rt_id = item["id"]
                    print(f"ℹ️ Request type {request_type['name']} already exists (ID: {rt_id})")
                    break
    except Exception as e:
        print(f"⚠️ Failed to create request type: {e}")

    if rt_id:
        # 4. Configure Parameters
        config = {
            "name": "Flight_Booking_Order",
            "description": "Used by agents to issue flight tickets",
            "is_active": True,
            "parameters": [
                {"name": "Passenger_Name", "type": "string", "is_required": True, "description": "Full name of the passenger"},
                {"name": "Passport_ID", "type": "string", "is_required": True, "description": "Passport or ID Number"},
                {"name": "Flight_Number", "type": "string", "is_required": True, "description": "Flight Number (e.g. W5-102)"},
                {"name": "PNR", "type": "string", "is_required": True, "description": "Passenger Name Record (Reservation Code)"}
            ]
        }
        try:
            resp = requests.put(f"{BASE_URL}/request-types/{rt_id}/configure", json=config, headers=headers)
            resp.raise_for_status()
            print("✅ Configured Flight_Booking_Order parameters.")
        except Exception as e:
            print(f"⚠️ Failed to configure parameters: {e}")

    # 5. Create Test User
    user_data = {
        "username": "agent001",
        "password": "agentPassword123!",
        "full_name": "Agency Sales Agent 01",
        "profile_type": "Sales_Agent",
        "is_active": True
    }
    try:
        resp = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
        if resp.status_code == 200 or resp.status_code == 201:
            print(f"✅ Created user: {user_data['username']}")
        elif resp.status_code == 400 or resp.status_code == 409:
            print(f"ℹ️ User {user_data['username']} already exists.")
        else:
            resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ Failed to create user: {e}")

    print("\n🏁 Scenario setup completed.")

if __name__ == "__main__":
    setup_scenario()
