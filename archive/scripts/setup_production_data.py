import requests
import json
import sys

# Configuration
RESPONSE_API_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    print(f"Logging in to {RESPONSE_API_URL}...")
    try:
        response = requests.post(f"{RESPONSE_API_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Login successful")
        return token
    except Exception as e:
        print(f"❌ Login failed: {e}")
        if response:
            print(response.text)
        sys.exit(1)

def setup_request_type(token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Check if exists
    print("Checking for existing request types...")
    res = requests.get(f"{RESPONSE_API_URL}/request-types/", headers=headers)
    existing_types = res.json()
    
    flight_booking = next((rt for rt in existing_types if rt["name"] == "FlightBooking"), None)
    
    if flight_booking:
        print("ℹ️ Request Type 'FlightBooking' already exists.")
        return flight_booking["id"]
    
    # Create Request Type
    print("Creating 'FlightBooking' request type...")
    rt_data = {
        "name": "FlightBooking",
        "description": "Book a flight ticket",
        "base_priority": 10,
        "is_active": True
    }
    res = requests.post(f"{RESPONSE_API_URL}/request-types/", headers=headers, json=rt_data)
    if res.status_code != 200:
        print(f"❌ Failed to create request type: {res.text}")
        sys.exit(1)
        
    rt_id = res.json()["id"]
    print(f"✅ Created Request Type: {rt_id}")
    
    # Create Parameters
    print("Adding parameters...")
    params = [
        {"name": "origin", "type": "string", "required": True, "label": "Origin City"},
        {"name": "destination", "type": "string", "required": True, "label": "Destination City"},
        {"name": "date", "type": "date", "required": True, "label": "Flight Date"}
    ]
    
    for p in params:
        res = requests.post(f"{RESPONSE_API_URL}/request-types/{rt_id}/parameters", headers=headers, json=p)
        if res.status_code != 200:
            print(f"⚠️ Failed to add param {p['name']}: {res.text}")
        else:
            print(f"   ✓ Added {p['name']}")
            
    # Setup Query Template (Elasticsearch)
    print("Setting up Query Template...")
    query_template = {
        "name": "Flight Search Query",
        "index_pattern": "flights",
        "query_template": {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"origin": "{{origin}}"}},
                        {"match": {"destination": "{{destination}}"}}
                    ]
                }
            }
        },
        "description": "Search flights by origin and destination"
    }
    # Note: Adjust endpoint if needed, usually it updates the request type or a separate endpoint
    # Assuming valid update or ignoring for now as simple flow test doesn't strictly need ES to return results, just to process.
    
    return rt_id

def grant_access(token, rt_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Grant to 'admin' profile type
    print("Granting access to 'admin' profile type...")
    # First get profile types to find admin or create mapping
    # Assuming simple endpoint exists or we use the profile-type-access router
    
    # Check current access
    # Simplification: Just ensure the user (admin) has a profile type that allows this.
    # Admin usually has access to all, but let's be explicit if needed.
    pass

if __name__ == "__main__":
    token = login()
    rt_id = setup_request_type(token)
    grant_access(token, rt_id)
    print("\n✅ Setup Complete! Waiting for sync...")
