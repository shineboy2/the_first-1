#!/bin/bash
set -e

# Detect what service to run based on SERVICE_TYPE env var or container name
SERVICE_TYPE="${SERVICE_TYPE:-$(hostname)}"
echo "🚀 Starting Request Network - Service: $SERVICE_TYPE"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until PGPASSWORD=$REQUEST_DB_PASSWORD psql -h $REQUEST_DB_HOST -U $REQUEST_DB_USER -d $REQUEST_DB_NAME -c '\l' > /dev/null 2>&1; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✓ Database is ready"

# Only run migrations and initialization for API server
if [[ "$SERVICE_TYPE" == "api" || "$SERVICE_TYPE" == *"api"* ]]; then
    echo "📦 Running database migrations..."
    python -m alembic upgrade head
    echo "✓ Migrations completed"

    # Initialize default admin user if needed
    echo "👤 Initializing default admin user..."
    python << 'INIT_SCRIPT'
import sys
import asyncio
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup paths
_api_dir = Path(__file__).resolve().parent
_project_root = _api_dir.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_api_dir))

from setup.initialization import initialize_database

async def main():
    try:
        result = await initialize_database()
        if result:
            logger.info("✓ Database initialization completed")
        else:
            logger.warning("⚠️  Database initialization had issues, continuing...")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't exit, the app might still work

asyncio.run(main())
INIT_SCRIPT

    echo ""
    echo "✅ Startup preparation completed"
    echo "🎯 Starting uvicorn server..."
    echo ""
    exec uvicorn main:app --host 0.0.0.0 --port 8000

elif [[ "$SERVICE_TYPE" == "celery-worker" || "$SERVICE_TYPE" == "worker" ]]; then
    echo "👷 Starting Celery Worker..."
    exec celery -A workers.celery_app worker -l info --concurrency=4

elif [[ "$SERVICE_TYPE" == "celery-beat" || "$SERVICE_TYPE" == "beat" ]]; then
    echo "⏰ Starting Celery Beat Scheduler..."
    exec celery -A workers.celery_app beat -l info

elif [[ "$SERVICE_TYPE" == "flower" ]]; then
    echo "🌸 Starting Flower Celery Monitor..."
    exec celery -A workers.celery_app flower --port=5555 --basic_auth=${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin123}

else
    echo "❌ Unknown service: $SERVICE_TYPE"
    echo "🎯 Defaulting to uvicorn server..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000
fi
