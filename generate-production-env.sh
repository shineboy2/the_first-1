#!/bin/bash

# تولید فایل‌های .env برای پروداکشن
# این اسکریپت توسط prepare_vm_template.sh و reconfigure_production_ips.sh اجرا می‌شود
# شما نیازی به اجرای دستی ندارید

if [ ! -f "deployment-config.env" ]; then
    echo "❌ فایل deployment-config.env یافت نشد!"
    exit 1
fi

source deployment-config.env

# تولید request-network/.env
if [ -d "request-network" ]; then
cat > request-network/.env << EOF
DB_USER=request_user
DB_PASSWORD=secret
DB_NAME=request_db
REQUEST_DB_USER=request_user
REQUEST_DB_PASSWORD=secret
REQUEST_DB_NAME=request_db
REQUEST_DB_HOST=postgres
REQUEST_DB_PORT=5432

REDIS_PASSWORD=secret
REDIS_URL=redis://:secret@redis:6379/0
CELERY_BROKER_URL=redis://:secret@redis:6379/0
CELERY_RESULT_BACKEND=redis://:secret@redis:6379/1

SECRET_KEY=supersecretkey_change_in_production

FTP_HOST=${FTP_HOST}
FTP_PORT=${FTP_PORT:-21}
FTP_USER=${FTP_USER}
FTP_PASSWORD=${FTP_PASSWORD}
FTP_USE_TLS=false

BACKEND_CORS_ORIGINS=${REQUEST_CORS_ORIGINS:-http://localhost:3002}
API_PORT=8001
ADMIN_PORT=3002
FLOWER_PORT=5555
NEXT_PUBLIC_API_URL=${REQUEST_API_URL:-http://localhost:8001}
EOF
fi

# تولید response-network/.env
if [ -d "response-network" ]; then
cat > response-network/.env << EOF
DB_PASSWORD=secret
REDIS_PASSWORD=secret
SECRET_KEY=supersecretkey_change_in_production
FTP_HOST=${FTP_HOST}
FTP_USER=${FTP_USER}
FTP_PASSWORD=${FTP_PASSWORD}
BACKEND_CORS_ORIGINS=["http://localhost:3000","${RESPONSE_API_URL:-http://localhost:8000}"]
NEXT_PUBLIC_API_URL=${RESPONSE_API_URL:-http://localhost:8000}
EOF
fi

echo "✅ فایل‌های .env تولید شدند"