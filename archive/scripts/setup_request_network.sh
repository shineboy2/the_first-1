#!/bin/bash
# Entrypoint for Request Network development

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "📦 Setting up Request Network (Secondary Network)..."
echo ""

cd "${SCRIPT_DIR}/request-network/api"

echo "🔄 Running database migrations for Request Network..."
python -m alembic upgrade head

echo ""
echo "🌱 Initializing Request Network..."
cd "${SCRIPT_DIR}"
python manage_db.py seed --network request

echo ""
echo "✅ Request Network setup complete!"
echo ""
echo "To start services, run:"
echo "  API:    PYTHONPATH=${SCRIPT_DIR} python -m uvicorn main:app --host 0.0.0.0 --port 8001"
echo "  Worker: PYTHONPATH=${SCRIPT_DIR} python -m celery -A workers.celery_app worker"
echo "  Beat:   PYTHONPATH=${SCRIPT_DIR} python -m celery -A workers.celery_app beat"
echo ""
echo "ℹ️  Users are automatically synced from Response Network via import workers"
echo ""

