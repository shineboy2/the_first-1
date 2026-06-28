import sys, os, asyncio, json
import requests
from datetime import timedelta

# Add app to path to import auth logic
sys.path.append("/app")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from models.user import User
from auth.security import create_access_token
from core.config import settings

# This async function just gets a token
async def get_admin_token():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user:
            token_data = {"user_id": str(user.id), "scopes": ["admin"]}
            return create_access_token(data=token_data, expires_delta=timedelta(hours=2))
    return None

token = asyncio.run(get_admin_token())
if not token:
    print("Failed to get admin token")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

BASE_URL = "http://localhost:8000/api/v1"

print("1. Creating External API for Mediastack News...")
ext_api_payload = {
    "name": "mediastack_news",
    "description": "Mediastack Live News API",
    "endpoint_url": "http://api.mediastack.com/v1/news?access_key=ae090de60c7de5960379780a82f29347",
    "http_method": "GET",
    "is_active": True,
    "auth_type": "static_key",
    "static_headers": {},
    "auth_config": {}
}

resp = requests.post(f"{BASE_URL}/external-apis/", json=ext_api_payload, headers=headers)
if resp.status_code == 201:
    ext_api_id = resp.json()["id"]
    print("External API created:", ext_api_id)
elif resp.status_code == 400 and "already exists" in resp.text:
    resp2 = requests.get(f"{BASE_URL}/external-apis/", headers=headers)
    apis = resp2.json()
    ext_api_id = next(a["id"] for a in apis if a["name"] == "mediastack_news")
    print("External API already exists:", ext_api_id)
else:
    print("Failed to create external API:", resp.text)
    sys.exit(1)

requests.patch(f"{BASE_URL}/external-apis/profile-types/default/access", json={"allowed_external_apis": ["mediastack_news"]}, headers=headers)

print("2. Creating Request Types...")
request_types = [
    {
        "name": "search_flights",
        "description": "Search flights by airline or airport",
        "method": "elasticsearch",
        "indices": ["flights"],
        "template": {"query": {"bool": {"must": [{"match_all": {}}]}}},
        "params": [
            {"name": "airline", "type": "string", "is_required": False, "description": "Airline name", "parameter_type": "query", "placeholder_key": "airline"},
            {"name": "status", "type": "string", "is_required": False, "description": "Flight status", "parameter_type": "query", "placeholder_key": "status"}
        ]
    },
    {
        "name": "search_passengers",
        "description": "Search passenger records",
        "method": "elasticsearch",
        "indices": ["passengers"],
        "template": {"query": {"match_all": {}}},
        "params": []
    },
    {
        "name": "search_reservations",
        "description": "Search flight reservations",
        "method": "elasticsearch",
        "indices": ["reservations"],
        "template": {"query": {"match_all": {}}},
        "params": []
    },
    {
        "name": "mediastack_news",
        "description": "Get real-time news articles",
        "method": "external_api",
        "ext_api_id": ext_api_id,
        "template": {},
        "params": [
            {"name": "categories", "type": "string", "is_required": False, "description": "Comma-separated categories", "parameter_type": "query", "placeholder_key": "categories"},
            {"name": "countries", "type": "string", "is_required": False, "description": "Comma-separated country codes", "parameter_type": "query", "placeholder_key": "countries"},
            {"name": "keywords", "type": "string", "is_required": False, "description": "Keywords to search", "parameter_type": "query", "placeholder_key": "keywords"},
            {"name": "languages", "type": "string", "is_required": False, "description": "Languages", "parameter_type": "query", "placeholder_key": "languages"},
            {"name": "limit", "type": "integer", "is_required": False, "description": "Max number of results", "parameter_type": "query", "placeholder_key": "limit"}
        ]
    }
]

for rt in request_types:
    print(f"Creating request type {rt['name']}...")
    init_payload = {
        "name": rt["name"],
        "description": rt["description"],
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/request-types/", json=init_payload, headers=headers)
    if resp.status_code == 201:
        rt_id = resp.json()["id"]
    elif resp.status_code == 400 and "already exists" in resp.text:
        resp_list = requests.get(f"{BASE_URL}/request-types/", headers=headers)
        rt_id = next(item["id"] for item in resp_list.json() if item["name"] == rt["name"])
    else:
        print(f"Failed to create {rt['name']}:", resp.text)
        continue
    
    params_payload = {
        "execution_method": rt["method"],
        "max_items_per_request": 100,
        "parameters": rt["params"]
    }
    if rt["method"] == "external_api":
        params_payload["external_api_id"] = rt["ext_api_id"]
    elif rt["method"] == "elasticsearch":
        params_payload["available_indices"] = rt["indices"]
    
    resp_cfg = requests.put(f"{BASE_URL}/request-types/{rt_id}/configure", json=params_payload, headers=headers)
    if resp_cfg.status_code != 200:
        print(f"Failed to configure params for {rt['name']}:", resp_cfg.text)
    
    query_payload = {
        "elasticsearch_query_template": rt["template"]
    }
    resp_q = requests.put(f"{BASE_URL}/request-types/{rt_id}/query", json=query_payload, headers=headers)
    
    access_payload = {
        "profile_type_ids": ["default"],
        "max_requests_per_day": 1000,
        "max_requests_per_month": 30000,
        "is_active": True
    }
    resp_acc = requests.post(f"{BASE_URL}/request-types/{rt_id}/profile-access", json=access_payload, headers=headers)

print("Done setting up request types.")
