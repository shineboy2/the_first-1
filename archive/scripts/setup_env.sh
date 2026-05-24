#!/bin/bash
# Entrypoint for development: ensures PYTHONPATH is set correctly

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add project root to PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "📦 Setting up Response Network (Master Network)..."
echo ""

# Navigate to Response Network API
cd "${SCRIPT_DIR}/response-network/api"

# Run migrations
echo "🔄 Running database migrations..."
python -m alembic upgrade head

# Verify models import
echo "🔍 Verifying model imports..."
if python -c "from models.user import User; print('✓ Models imported')" 2>/dev/null; then
    echo "  ✓ Models imported successfully"
else
    echo "  ✗ Failed to import models - PYTHONPATH issue"
    exit 1
fi

# Seed initial data
echo ""
echo "🌱 Seeding initial data..."
cd "${SCRIPT_DIR}"
python manage_db.py seed --network response

echo ""
echo "✅ Response Network setup complete!"
echo ""
echo "To start services, run:"
echo "  API:    PYTHONPATH=${SCRIPT_DIR} python -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  Worker: PYTHONPATH=${SCRIPT_DIR} python -m celery -A workers.celery_app worker"
echo "  Beat:   PYTHONPATH=${SCRIPT_DIR} python -m celery -A workers.celery_app beat"
echo ""
echo "📝 Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin@123456"
echo ""

