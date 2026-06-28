#!/bin/bash
set -x

REDIS_PASS="redis_secure_pass"

# Inject fake captcha for Response Network into Redis
docker exec sim-resp-redis redis-cli -a "$REDIS_PASS" SETEX captcha:11111111-1111-1111-1111-111111111111 300 12345 > /dev/null 2>&1

# Login to Response Network
RESP_LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=123456&captcha_id=11111111-1111-1111-1111-111111111111&captcha_solution=12345")
RESP_TOKEN=$(echo $RESP_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Response Network Token: $RESP_TOKEN"

# Clean up existing data to avoid conflicts
docker exec sim-resp-db psql -U response_user -d response_db -c "DELETE FROM request_types; DELETE FROM file_request_configs; DELETE FROM ftp_profiles; DELETE FROM external_apis;"

# 1. Create FTP Profile in Response Network
echo "Creating FTP Profile in Response Network..."
FTP_PROFILE=$(curl -s -X POST http://localhost:8000/api/v1/ftp-profiles/ \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sim-ftp-sync",
    "display_name": "sim-ftp-sync",
    "host": "ftp-req",
    "port": 21,
    "username": "ftp_user",
    "password": "ftp_password",
    "use_tls": false,
    "remote_path": "/",
    "is_active": true
  }')
echo $FTP_PROFILE
FTP_PROFILE_ID=$(echo $FTP_PROFILE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 2. Configure File Request Config (for FTP sync)
echo "Creating File Request Config in Response Network..."
FILE_CONFIG=$(curl -s -X POST http://localhost:8000/api/v1/file-request-configs/ \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sync_to_request_network",
    "display_name": "Sync to Request Network",
    "content_format": "json",
    "direction": "both",
    "filename_template": "sync_{type}_{timestamp}.json",
    "send_ftp_profile_id": "'$FTP_PROFILE_ID'",
    "receive_ftp_profile_id": "'$FTP_PROFILE_ID'",
    "is_active": true
  }')
echo $FILE_CONFIG
CONFIG_ID=$(echo $FILE_CONFIG | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 3. Create External API (JSONPlaceholder) in Response Network
echo "Creating External API in Response Network..."
EXT_API=$(curl -s -X POST http://localhost:8000/api/v1/external-apis/ \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JSONPlaceholder",
    "endpoint_url": "https://jsonplaceholder.typicode.com",
    "description": "Mock REST API for testing",
    "auth_type": "none",
    "is_active": true,
    "timeout_seconds": 30,
    "retry_count": 3
  }')
echo $EXT_API
API_ID=$(echo $EXT_API | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 4. Create Request Types in Response Network (One External API, One Database)
echo "Creating Request Types..."
# 4.1 Users endpoint from JSONPlaceholder
REQ_TYPE_1=$(curl -s -X POST http://localhost:8000/api/v1/request-types/ \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_external_users",
    "description": "Get users from external JSONPlaceholder API",
    "is_active": false,
    "execution_method": "external_api"
  }')
echo $REQ_TYPE_1
REQ_TYPE_1_ID=$(echo $REQ_TYPE_1 | grep -o '"id":"[^"]*' | cut -d'"' -f4)

curl -s -X PUT http://localhost:8000/api/v1/request-types/$REQ_TYPE_1_ID/params \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "is_public": true,
    "max_items_per_request": 100,
    "available_indices": ["users"],
    "parameters": [
      {
        "name": "userId",
        "description": "ID of the user to fetch",
        "parameter_type": "integer",
        "is_required": false,
        "placeholder_key": "userId"
      }
    ],
    "execution_method": "external_api",
    "external_api_id": "'$API_ID'",
    "file_request_config_id": "'$CONFIG_ID'"
  }'

# 4.2 Standard ES search
REQ_TYPE_2=$(curl -s -X POST http://localhost:8000/api/v1/request-types/ \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "local_database_search",
    "description": "Search in the local ElasticSearch database",
    "is_active": false,
    "execution_method": "elasticsearch"
  }')
echo $REQ_TYPE_2
REQ_TYPE_2_ID=$(echo $REQ_TYPE_2 | grep -o '"id":"[^"]*' | cut -d'"' -f4)

curl -s -X PUT http://localhost:8000/api/v1/request-types/$REQ_TYPE_2_ID/query \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "elasticsearch_query_template": {"query": {"match": {"name": "{query_string}"}}}
  }'

curl -s -X PUT http://localhost:8000/api/v1/request-types/$REQ_TYPE_2_ID/params \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "is_public": true,
    "max_items_per_request": 100,
    "available_indices": ["passengers"],
    "parameters": [
      {
        "name": "query_string",
        "description": "Text to search",
        "parameter_type": "string",
        "is_required": true,
        "placeholder_key": "query"
      }
    ],
    "execution_method": "elasticsearch",
    "file_request_config_id": "'$CONFIG_ID'"
  }'

echo "Triggering export to sync Request Types to Request Network..."
curl -s -X POST http://localhost:8000/api/v1/settings/system/trigger_export \
  -H "Authorization: Bearer $RESP_TOKEN" \
  -H "Content-Type: application/json"

echo "Done!"
