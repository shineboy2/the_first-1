#!/usr/bin/env python3
"""
Create sample request types for Elasticsearch search
"""

import requests
import json

BASE_URL = "http://192.168.214.141:8000/api/v1"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123456"

def login():
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return None
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return headers

def create_request_type(headers, name, description):
    data = {
        "name": name,
        "description": description,
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/request-types/", json=data, headers=headers)
    if resp.status_code == 201:
        rt_id = resp.json()["id"]
        print(f"✅ Created request type '{name}' (ID: {rt_id})")
        return rt_id
    else:
        print(f"❌ Failed to create '{name}': {resp.status_code} - {resp.text}")
        return None

def configure_params(headers, rt_id, params_config):
    resp = requests.put(f"{BASE_URL}/request-types/{rt_id}/configure", json=params_config, headers=headers)
    if resp.status_code == 200:
        print(f"✅ Configured parameters for {rt_id}")
    else:
        print(f"❌ Failed to configure params: {resp.status_code} - {resp.text}")

def update_query(headers, rt_id, query_config):
    resp = requests.put(f"{BASE_URL}/request-types/{rt_id}/query", json=query_config, headers=headers)
    if resp.status_code == 200:
        print(f"✅ Updated query for {rt_id}")
    else:
        print(f"❌ Failed to update query: {resp.status_code} - {resp.text}")

def get_request_types(headers):
    resp = requests.get(f"{BASE_URL}/request-types/", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Failed to get request types: {resp.text}")
        return []

def main():
    print("🚀 Creating sample request types for Elasticsearch search...")

    headers = login()
    if not headers:
        return

    # 1. Flight Search Request Type
    print("\n📋 Creating Flight Search Request Type...")
    rt_id = create_request_type(headers, "Flight_Search", "Search for flights by number or route")
    if rt_id:
        params_config = {
            "available_indices": ["flights"],
            "parameters": [
                {"name": "Flight Number", "parameter_type": "string", "is_required": False, "placeholder_key": "flight_number"},
                {"name": "Departure Airport", "parameter_type": "string", "is_required": False, "placeholder_key": "departure_airport"},
                {"name": "Arrival Airport", "parameter_type": "string", "is_required": False, "placeholder_key": "arrival_airport"},
                {"name": "Airline", "parameter_type": "string", "is_required": False, "placeholder_key": "airline"}
            ]
        }
        configure_params(headers, rt_id, params_config)

        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"flight_number": "{{flight_number}}"}},
                            {"match": {"departure_airport": "{{departure_airport}}"}},
                            {"match": {"arrival_airport": "{{arrival_airport}}"}},
                            {"match": {"airline": "{{airline}}"}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 10
            }
        }
        configure_query(headers, rt_id, query_config)

    # 2. Passenger Search Request Type
    print("\n👥 Creating Passenger Search Request Type...")
    rt_id = create_request_type(headers, "Passenger_Search", "Search for passengers by name or email")
    if rt_id:
        params_config = {
            "available_indices": ["passengers"],
            "parameters": [
                {"name": "First Name", "parameter_type": "string", "is_required": False, "placeholder_key": "first_name"},
                {"name": "Last Name", "parameter_type": "string", "is_required": False, "placeholder_key": "last_name"},
                {"name": "Email", "parameter_type": "string", "is_required": False, "placeholder_key": "email"},
                {"name": "Nationality", "parameter_type": "string", "is_required": False, "placeholder_key": "nationality"}
            ]
        }
        configure_params(headers, rt_id, params_config)

        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"first_name": "{{first_name}}" }} if "{{first_name}}" else None,
                            {"match": {"last_name": "{{last_name}}" }} if "{{last_name}}" else None,
                            {"match": {"email": "{{email}}" }} if "{{email}}" else None,
                            {"match": {"nationality": "{{nationality}}" }} if "{{nationality}}" else None
                        ]
                    }
                },
                "size": 10
            }
        }
        query_config["elasticsearch_query_template"]["query"]["bool"]["must"] = [
            item for item in query_config["elasticsearch_query_template"]["query"]["bool"]["must"] if item is not None
        ]
        configure_query(headers, rt_id, query_config)

    # 3. Reservation Search Request Type
    print("\n🎫 Creating Reservation Search Request Type...")
    rt_id = create_request_type(headers, "Reservation_Search", "Search for reservations by flight or passenger")
    if rt_id:
        params_config = {
            "available_indices": ["reservations"],
            "parameters": [
                {"name": "Flight Number", "parameter_type": "string", "is_required": False, "placeholder_key": "flight_number"},
                {"name": "Passenger Email", "parameter_type": "string", "is_required": False, "placeholder_key": "passenger_email"},
                {"name": "Reservation ID", "parameter_type": "string", "is_required": False, "placeholder_key": "reservation_id"},
                {"name": "Status", "parameter_type": "string", "is_required": False, "placeholder_key": "status"}
            ]
        }
        configure_params(headers, rt_id, params_config)

        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"flight_number": "{{flight_number}}" }} if "{{flight_number}}" else None,
                            {"match": {"passenger_email": "{{passenger_email}}" }} if "{{passenger_email}}" else None,
                            {"match": {"reservation_id": "{{reservation_id}}" }} if "{{reservation_id}}" else None,
                            {"match": {"status": "{{status}}" }} if "{{status}}" else None
                        ]
                    }
                },
                "size": 10
            }
        }
        query_config["elasticsearch_query_template"]["query"]["bool"]["must"] = [
            item for item in query_config["elasticsearch_query_template"]["query"]["bool"]["must"] if item is not None
        ]
        configure_query(headers, rt_id, query_config)

    print("\n✅ All request types created successfully!")

if __name__ == "__main__":
    main()