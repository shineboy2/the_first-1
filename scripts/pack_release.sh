#!/bin/bash
set -e

# Define Output Directory
OUTPUT_DIR="dist"
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

echo "📦 Packaging Response Network..."
# Prepare temporary build dir
rm -rf /tmp/response_build
mkdir -p /tmp/response_build

# Copy Files
cp docker-compose.response.yml /tmp/response_build/docker-compose.yml
cp Dockerfile.response /tmp/response_build/Dockerfile.response
rsync -av --exclude='api/exports/*' --exclude='api/imports/*' \
    --exclude='admin-panel/node_modules' --exclude='admin-panel/.next' \
    --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' \
    response-network /tmp/response_build/
rsync -av scripts /tmp/response_build/
mkdir -p /tmp/response_build/shared_data

# Create .env.example if not exists (Basic template)
cat > /tmp/response_build/.env.example <<EOL
POSTGRES_USER=respuser
POSTGRES_PASSWORD=resppassword123
POSTGRES_DB=response_db
REDIS_URL=redis://redis-response:6379/0
ELASTICSEARCH_URL=http://elasticsearch:9200
NEXT_PUBLIC_API_URL=http://localhost:8000
EOL

# Tarball
tar -czf $OUTPUT_DIR/response-network-release.tar.gz -C /tmp/response_build .
echo "✅ Created $OUTPUT_DIR/response-network-release.tar.gz"


echo "📦 Packaging Request Network..."
# Prepare temporary build dir
rm -rf /tmp/request_build
mkdir -p /tmp/request_build

# Copy Files
cp docker-compose.request.yml /tmp/request_build/docker-compose.yml
cp Dockerfile.request-network /tmp/request_build/Dockerfile.request-network
rsync -av --exclude='api/exports/*' --exclude='api/imports/*' \
    --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' \
    request-network /tmp/request_build/
mkdir -p /tmp/request_build/shared_data

# Create .env.example
cat > /tmp/request_build/.env.example <<EOL
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=request_db
REDIS_URL=redis://redis-request:6379/0
EOL

# Tarball
tar -czf $OUTPUT_DIR/request-network-release.tar.gz -C /tmp/request_build .
echo "✅ Created $OUTPUT_DIR/request-network-release.tar.gz"

echo "🎉 Packaging Complete! Upload the files in '$OUTPUT_DIR' to your servers."
