#!/bin/bash
# Entrypoint script for Response Network API
set -e

export PYTHONPATH="/app:${PYTHONPATH}"

# Set default environment variables
export DB_HOST="${DB_HOST:-response_postgres}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-response_network}"
export DB_USER="${DB_USER:-postgres}"
export DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if python -c "import psycopg2; psycopg2.connect('dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD host=$DB_HOST port=$DB_PORT')" 2>/dev/null; then
        echo "✓ Database is ready"
        break
    fi
    echo "Attempt $i/30 - Database not ready yet..."
    sleep 2
done

# Initialize database
echo "📦 Initializing Response Network database..."
cd /app/response-network/api
python manage.py init || true
python manage.py migrate || true
python manage.py seed || true

echo "✓ Initialization complete"
echo "🚀 Starting FastAPI server..."

# Run the main FastAPI app
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
