#!/usr/bin/env python3
"""
Update sample request types for Elasticsearch search
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
    print("🚀 Updating sample request types for Elasticsearch search...")

    headers = login()
    if not headers:
        return

    # Get existing request types
    rts = get_request_types(headers)
    rt_map = {rt["name"]: rt["id"] for rt in rts}

    # 1. Flight Search Request Type
    print("\n📋 Updating Flight Search Request Type...")
    rt_id = rt_map.get("Flight_Search")
    if rt_id:
        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "should": [
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
        update_query(headers, rt_id, query_config)
    else:
        print("Flight_Search not found")

    # 2. Passenger Search Request Type
    print("\n👥 Updating Passenger Search Request Type...")
    rt_id = rt_map.get("Passenger_Search")
    if rt_id:
        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"first_name": "{{first_name}}"}},
                            {"match": {"last_name": "{{last_name}}"}},
                            {"match": {"email": "{{email}}"}},
                            {"match": {"nationality": "{{nationality}}"}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 10
            }
        }
        update_query(headers, rt_id, query_config)

    # 3. Reservation Search Request Type
    print("\n🎫 Updating Reservation Search Request Type...")
    rt_id = rt_map.get("Reservation_Search")
    if rt_id:
        query_config = {
            "elasticsearch_query_template": {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"flight_number": "{{flight_number}}"}},
                            {"match": {"passenger_email": "{{passenger_email}}"}},
                            {"match": {"reservation_id": "{{reservation_id}}"}},
                            {"match": {"status": "{{status}}"}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 10
            }
        }
        update_query(headers, rt_id, query_config)

    print("\n✅ All request types updated successfully!")

if __name__ == "__main__":
    main()