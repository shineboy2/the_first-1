#!/bin/bash
set -e

# =============================================================================
# Build and Export Docker Images for Production
# =============================================================================

echo "============================================================"
echo "🚀 Building and Exporting Docker Images"
echo "============================================================"

# Ensure output directory exists
OUTPUT_DIR="exports/docker_images"
mkdir -p "$OUTPUT_DIR"

# Request Network
echo "📦 Building Request Network images..."
cd request-network
docker compose -f docker-compose.yml build
cd ..

# Response Network
echo "📦 Building Response Network images..."
cd response-network
docker compose -f docker-compose.yml build
cd ..

echo "💾 Saving images to tar files (this may take a few minutes)..."

# Find image names (assuming standard docker-compose naming)
REQUEST_API_IMG="request-network-api:latest"
REQUEST_ADMIN_IMG="request-network-admin-panel:latest"
REQUEST_CELERY_WORKER_IMG="request-network-celery-worker:latest"
REQUEST_CELERY_BEAT_IMG="request-network-celery-beat:latest"
REQUEST_FLOWER_IMG="request-network-flower:latest"

RESPONSE_API_IMG="response-network:latest"
RESPONSE_ADMIN_IMG="response-network-admin-panel:latest"

# Note: request network shares the same base image for api, worker, beat, flower (they all build from same Dockerfile in context: . )
# Wait, let's look at request-network/docker-compose.yml:
# api: build context .
# celery-worker: build context .
# celery-beat: build context .
# flower: build context .
# admin-panel: build context ./admin-panel
# They might be named request-network-api, request-network-celery-worker, etc. but it's redundant to export all of them if they are exactly the same image.
# Actually, let's just save the images that docker-compose built.

# To be safe, let's just save by the image names defined or the compose-generated names.
# For response-network, the image name is explicitly set to `response-network:latest` for api, celery-worker, celery-beat, flower.
# For request-network, there is no `image:` field, so compose names them `request-network-api`, `request-network-celery-worker`, etc.

# Let's tag the request-network base image to make it easier
docker tag request-network-api request-network:latest

echo "Exporting Request Network Base (API/Worker/Beat/Flower)..."
docker save request-network:latest -o $OUTPUT_DIR/request-network-backend.tar

echo "Exporting Request Network Admin Panel..."
docker save request-network-admin-panel:latest -o $OUTPUT_DIR/request-network-admin.tar

echo "Exporting Response Network Base (API/Worker/Beat/Flower)..."
docker save response-network:latest -o $OUTPUT_DIR/response-network-backend.tar

echo "Exporting Response Network Admin Panel..."
docker save response-network-admin-panel:latest -o $OUTPUT_DIR/response-network-admin.tar

echo "🗜️ Compressing tar files..."
gzip -f $OUTPUT_DIR/*.tar

echo "✅ All images exported to $OUTPUT_DIR"
echo "You can copy these .tar.gz files to your production server and run:"
echo "  docker load -i <file.tar.gz>"
