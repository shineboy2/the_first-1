import os
import sys
import json
import logging
from fastapi.testclient import TestClient

# Add api to path so imports work
sys.path.insert(0, os.path.abspath("api"))

from main import app
from auth.utils import create_access_token

client = TestClient(app)

# Generate a token directly
token = create_access_token(data={"sub": "admin"})

response = client.get("/api/v1/request-types/", headers={"Authorization": f"Bearer {token}"})
print(f"Status Code: {response.status_code}")
try:
    data = response.json()
    print(f"Number of request types: {len(data)}")
    for rt in data:
        print(f" - {rt.get('name')} (Active: {rt.get('is_active')})")
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print(response.text)

