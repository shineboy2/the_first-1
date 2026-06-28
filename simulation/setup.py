import requests
import json
import time
import os

# Connect to Redis to set captcha
os.system("docker exec sim-resp-redis redis-cli -a 'redis_secure_pass' SETEX captcha:11111111-1111-1111-1111-111111111111 300 12345 > /dev/null 2>&1")
os.system("docker exec sim-req-redis redis-cli -a 'redis_secure_pass' SETEX captcha:11111111-1111-1111-1111-111111111111 300 12345 > /dev/null 2>&1")

# Login Response Network
resp = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "admin",
    "password": "123456",
    "captcha_id": "11111111-1111-1111-1111-111111111111",
    "captcha_solution": "12345"
})
resp.raise_for_status()
resp_token = resp.json()["access_token"]
resp_headers = {"Authorization": f"Bearer {resp_token}", "Content-Type": "application/json"}

# Login Request Network
req = requests.post("http://localhost:8001/api/v1/auth/login", data={
    "username": "admin",
    "password": "123456",
    "captcha_id": "11111111-1111-1111-1111-111111111111",
    "captcha_solution": "12345"
})
req.raise_for_status()
req_token = req.json()["access_token"]
req_headers = {"Authorization": f"Bearer {req_token}", "Content-Type": "application/json"}

# Cleanup
print("Cleaning up database...")
os.system('docker exec sim-resp-db psql -U response_user -d response_db -c "DELETE FROM request_type_parameters; DELETE FROM request_types; DELETE FROM file_request_configs; DELETE FROM ftp_profiles; DELETE FROM external_apis; DELETE FROM settings;"')
os.system('docker exec sim-req-db psql -U request_user -d request_db -c "DELETE FROM settings;"')
time.sleep(2)

print("Creating FTP Profile in Response Network...")
ftp_resp = requests.post("http://localhost:8000/api/v1/ftp-profiles/", headers=resp_headers, json={
    "name": "sim-ftp-sync",
    "display_name": "sim-ftp-sync",
    "host": "ftp-resp",
    "port": 21,
    "username": "ftpuser",
    "password": "ftppass",
    "use_tls": False,
    "remote_path": "/",
    "is_active": True
})
ftp_resp.raise_for_status()
ftp_id = ftp_resp.json()["id"]

print("Configuring Export Settings in Response Network...")
cfg_resp = requests.post("http://localhost:8000/api/v1/admin/exports/config/request_types_export", headers=resp_headers, json={
    "operation_type": "request_types_export",
    "enabled": True,
    "format": "json",
    "destination_type": "ftp",
    "ftp_profile_id": ftp_id,
    "ftp_path": "/"
})
cfg_resp.raise_for_status()

print("Configuring Import Settings in Request Network...")
cfg_req = requests.post("http://localhost:8001/api/v1/admin/imports/config/request_types_import", headers=req_headers, json={
    "enabled": True,
    "format": "json",
    "destination_type": "ftp",
    "ftp_host": "ftp-req",
    "ftp_port": 21,
    "ftp_user": "ftpuser",
    "ftp_password": "ftppass",
    "ftp_path": "/request_types",
    "ftp_use_tls": False
})
cfg_req.raise_for_status()

print("Creating File Request Config...")
file_config_resp = requests.post("http://localhost:8000/api/v1/file-request-configs/", headers=resp_headers, json={
    "name": "sync_to_request_network",
    "display_name": "Sync to Request Network",
    "content_format": "json",
    "direction": "both",
    "filename_template": "sync_{type}_{timestamp}.json",
    "send_ftp_profile_id": ftp_id,
    "receive_ftp_profile_id": ftp_id,
    "is_active": True
})
file_config_resp.raise_for_status()
config_id = file_config_resp.json()["id"]

print("Creating External API...")
ext_api_resp = requests.post("http://localhost:8000/api/v1/external-apis/", headers=resp_headers, json={
    "name": "JSONPlaceholder",
    "endpoint_url": "https://jsonplaceholder.typicode.com",
    "description": "Mock REST API for testing",
    "auth_type": "none",
    "is_active": True,
    "timeout_seconds": 30,
    "retry_count": 3
})
ext_api_resp.raise_for_status()
api_id = ext_api_resp.json()["id"]

print("Creating Request Types...")

# 1. External API type
rt1_resp = requests.post("http://localhost:8000/api/v1/request-types/", headers=resp_headers, json={
    "name": "get_external_users",
    "description": "Get users from external JSONPlaceholder API",
    "is_active": False,
    "execution_method": "external_api"
})
rt1_resp.raise_for_status()
rt1_id = rt1_resp.json()["id"]

rt1_params = requests.put(f"http://localhost:8000/api/v1/request-types/{rt1_id}/params", headers=resp_headers, json={
    "is_active": True,
    "is_public": True,
    "max_items_per_request": 100,
    "available_indices": ["users"],
    "parameters": [
      {
        "name": "userId",
        "description": "ID of the user to fetch",
        "parameter_type": "integer",
        "is_required": False,
        "placeholder_key": "userId"
      }
    ],
    "execution_method": "external_api",
    "external_api_id": api_id,
    "file_request_config_id": config_id
})
rt1_params.raise_for_status()

# 2. Elasticsearch type
rt2_resp = requests.post("http://localhost:8000/api/v1/request-types/", headers=resp_headers, json={
    "name": "local_database_search",
    "description": "Search in the local ElasticSearch database",
    "is_active": False,
    "execution_method": "elasticsearch"
})
rt2_resp.raise_for_status()
rt2_id = rt2_resp.json()["id"]

rt2_query = requests.put(f"http://localhost:8000/api/v1/request-types/{rt2_id}/query", headers=resp_headers, json={
    "elasticsearch_query_template": {"query": {"match": {"name": "{query_string}"}}}
})
rt2_query.raise_for_status()

rt2_params = requests.put(f"http://localhost:8000/api/v1/request-types/{rt2_id}/params", headers=resp_headers, json={
    "is_active": True,
    "is_public": True,
    "max_items_per_request": 100,
    "available_indices": ["passengers"],
    "parameters": [
      {
        "name": "query_string",
        "description": "Text to search",
        "parameter_type": "string",
        "is_required": True,
        "placeholder_key": "query"
      }
    ],
    "execution_method": "elasticsearch",
    "file_request_config_id": config_id
})
rt2_params.raise_for_status()


print("Triggering export...")
export = requests.post("http://localhost:8000/api/v1/settings/system/trigger_export", headers=resp_headers)
export.raise_for_status()

# Wait 2 seconds for export to finish
time.sleep(2)

print("Triggering import in Request Network...")
import_req = requests.post("http://localhost:8001/api/v1/admin/imports/test/request_types_import", headers=req_headers)
if import_req.status_code != 200:
    print(import_req.json())
else:
    print("Import triggered:", import_req.json())

print("Done!")
