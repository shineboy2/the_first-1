# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
admin_token = None
user_token = None

async def login(client: httpx.AsyncClient, email: str, password: str) -> Optional[str]:
    try:
        response = await client.post(
            f"{BASE_URL}/api/v1/api/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "password",
                "username": email,
                "password": password
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        print(f"Login failed for {email}: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

async def test_endpoint(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    json_data: Optional[Dict] = None,
    expected_status: int = 200
) -> bool:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        if method.upper() == "GET":
            response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
        elif method.upper() == "POST":
            response = await client.post(f"{BASE_URL}{endpoint}", headers=headers, json=json_data)
        elif method.upper() == "PUT":
            response = await client.put(f"{BASE_URL}{endpoint}", headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            response = await client.delete(f"{BASE_URL}{endpoint}, headers=headers")
        else:
            print(f"Unsupported method: {method}")
            return False

        print(f"Testing {method} {endpoint}")
        if response.status_code != expected_status:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        print(f"✅ Success")
        return True
    except Exception as e:
        print(f"❌ Failed with error: {e}")
        return False

async def main():
    global admin_token, user_token
    
    print("\n🔍 Starting API endpoint tests...")
    
    async with httpx.AsyncClient() as client:
        # First test the health check endpoint (no auth required)
        print("\n📡 Testing health endpoint...")
        await test_endpoint(client, "GET", "/api/v1/system/health", expected_status=200)
        
        # Get authentication tokens
        print("\n🔐 Testing authentication...")
        admin_token = await login(client, "admin@example.com", "admin123")
        if not admin_token:
            print("❌ Failed to get admin token, some tests will be skipped")
        
        user_token = await login(client, "test@example.com", "test123")
        if not user_token:
            print("❌ Failed to get user token, some tests will be skipped")

        # Test various endpoints
        print("\n🧪 Testing authenticated endpoints...")
        
        # System endpoints
        if admin_token:
            await test_endpoint(client, "GET", "/api/v1/system/health", admin_token)
            await test_endpoint(client, "GET", "/api/v1/system/settings", admin_token)
        
        # User endpoints
        if admin_token:
            await test_endpoint(client, "GET", "/api/v1/users/me", admin_token)
            await test_endpoint(client, "GET", "/api/v1/users", admin_token)
        
        if user_token:
            await test_endpoint(client, "GET", "/api/v1/users/me", user_token)
        
        # Request type endpoints
        if admin_token:
            await test_endpoint(client, "GET", "/api/v1/requests/types", admin_token)
            
            # Create a test request type
            test_type = {
                "name": "Test Request Type",
                "description": "Test description",
                "is_active": True,
                "max_items_per_request": 10,
                "version": "1.0.0"
            }
            await test_endpoint(
                client, "POST", "/api/v1/requests/types",
                admin_token, json_data=test_type
            )

if __name__ == "__main__":
    asyncio.run(main())