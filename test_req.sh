#!/bin/bash
TOKEN=$(curl -s -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r .access_token)
echo "Token: $TOKEN"

curl -s -X GET "http://localhost:8001/api/v1/request-types/" \
  -H "Authorization: Bearer $TOKEN" | jq .
