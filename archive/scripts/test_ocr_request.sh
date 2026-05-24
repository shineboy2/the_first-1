#!/bin/bash

# Login and get token
TOKEN=$(curl -s -X POST http://192.168.214.146:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Sample base64 image (small test image with text "Hello")
BASE64_IMAGE="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9Qz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC"

# Send OCR request
echo "Sending OCR request..."
curl -X POST "http://192.168.214.146:8000/api/v1/external-requests/ocr_space" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_name\": \"test_ocr_$(date +%s)\",
    \"base64Image\": \"$BASE64_IMAGE\",
    \"language\": \"eng\"
  }"

echo ""
echo "Request sent!"
