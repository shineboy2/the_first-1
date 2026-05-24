#!/bin/bash
# Local environment variables for running services outside Docker
# Source this file before running local services: source local-env.sh

# ==================== DATABASE ====================
export DB_NAME=response_network
export DB_USER=postgres
export DB_PASSWORD=your_secure_password_change_me
export DB_HOST=localhost
export DB_PORT=5432
export DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Mappings for core/config.py
export RESPONSE_DB_NAME=${DB_NAME}
export RESPONSE_DB_USER=${DB_USER}
export RESPONSE_DB_PASSWORD=${DB_PASSWORD}
export RESPONSE_DB_HOST=${DB_HOST}
export RESPONSE_DB_PORT=${DB_PORT}

# ==================== REDIS ====================
export REDIS_PORT=6380
export REDIS_URL="redis://localhost:${REDIS_PORT}/0"

# ==================== CELERY ====================
export CELERY_BROKER_URL="redis://localhost:${REDIS_PORT}/0"
export CELERY_RESULT_BACKEND="redis://localhost:${REDIS_PORT}/1"

# ==================== ELASTICSEARCH ====================
export ELASTICSEARCH_URL="http://localhost:9200"

# ==================== API ====================
export API_V1_STR=/api/v1
export API_PORT=8000
export PROJECT_NAME="Response Network"

# ==================== SECURITY ====================
export SECRET_KEY="your_secret_key_change_me_at_least_32_chars"
export ALGORITHM=HS256

# ==================== FEATURES ====================
export DEBUG=false
export ENVIRONMENT=development
export DEV_MODE=true

# ==================== PATHS ====================
export EXPORT_DIR=exports

# ==================== LOGGING ====================
export LOG_LEVEL=INFO

echo "✓ Local environment variables loaded"
echo "  DATABASE_URL: ${DATABASE_URL}"
echo "  REDIS_URL: ${REDIS_URL}"
echo "  ELASTICSEARCH_URL: ${ELASTICSEARCH_URL}"
