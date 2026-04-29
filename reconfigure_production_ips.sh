#!/bin/bash

# =========================================================================
# اسکریپت تغییر IP های پروداکشن بدون rebuild
# =========================================================================
# این اسکریپت برای تغییر IP ها در VM های آماده شده طراحی شده است
# استفاده: ./reconfigure_production_ips.sh
# =========================================================================

set -e

echo "🔧 شروع تنظیم مجدد IP های پروداکشن..."
echo "================================================="

# دریافت IP های جدید از کاربر
read -p "IP سرور Response Network: " RESPONSE_HOST
read -p "IP سرور Request Network: " REQUEST_HOST  
read -p "IP سرور Elasticsearch: " ELASTICSEARCH_HOST
read -p "IP سرور FTP: " FTP_HOST

# تأیید IP ها
echo ""
echo "📋 IP های وارد شده:"
echo "   Response Network: $RESPONSE_HOST"
echo "   Request Network: $REQUEST_HOST"
echo "   Elasticsearch: $ELASTICSEARCH_HOST"
echo "   FTP: $FTP_HOST"
echo ""
read -p "آیا IP ها صحیح هستند؟ (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ عملیات لغو شد"
    exit 1
fi

# تشخیص نوع سرور (Response یا Request)
SERVER_TYPE=""
if [ -d "response-network" ]; then
    SERVER_TYPE="response"
    echo "🔍 سرور Response Network تشخیص داده شد"
elif [ -d "request-network" ]; then
    SERVER_TYPE="request"
    echo "🔍 سرور Request Network تشخیص داده شد"
else
    echo "❌ نوع سرور تشخیص داده نشد!"
    echo "این اسکریپت باید در پوشه اصلی پروژه اجرا شود"
    exit 1
fi

# بروزرسانی deployment-config.env
echo "📝 بروزرسانی deployment-config.env..."
cat > deployment-config.env << EOF
# Production Server IPs - Updated $(date)
RESPONSE_HOST=$RESPONSE_HOST
RESPONSE_USER=response
RESPONSE_PASS=1

REQUEST_HOST=$REQUEST_HOST
REQUEST_USER=request
REQUEST_PASS=1

ELASTICSEARCH_HOST=$ELASTICSEARCH_HOST
ELASTICSEARCH_USER=response
ELASTICSEARCH_PASS=1

# FTP Server (for file exchange between networks)
FTP_HOST=$FTP_HOST
FTP_PORT=21
FTP_USER=agftp
FTP_PASSWORD=agpass123

# API URLs for frontend
REQUEST_API_URL=http://$REQUEST_HOST:8001
RESPONSE_API_URL=http://$RESPONSE_HOST:8000

# CORS Origins
REQUEST_CORS_ORIGINS=http://localhost:3002,http://$REQUEST_HOST:3002
RESPONSE_CORS_ORIGINS=http://localhost:3000,http://$RESPONSE_HOST:3000
EOF

# تولید فایل‌های .env جدید
echo "🔄 تولید فایل‌های .env جدید..."
./generate-production-env.sh

# بروزرسانی بر اساس نوع سرور
if [ "$SERVER_TYPE" = "response" ]; then
    echo "🔧 تنظیم Response Network..."
    
    # بروزرسانی فایل .env
    sed -i "s|FTP_HOST=.*|FTP_HOST=$FTP_HOST|g" response-network/.env
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$RESPONSE_HOST:8000|g" response-network/.env
    sed -i "s|\"http://[^\"]*:3000\"|\"http://$RESPONSE_HOST:3000\"|g" response-network/.env
    
    echo "✅ Response Network تنظیم شد"
    
elif [ "$SERVER_TYPE" = "request" ]; then
    echo "🔧 تنظیم Request Network..."
    
    # بروزرسانی فایل .env
    sed -i "s|FTP_HOST=.*|FTP_HOST=$FTP_HOST|g" request-network/.env
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$REQUEST_HOST:8001|g" request-network/.env
    sed -i "s|http://[^,]*:3002|http://$REQUEST_HOST:3002|g" request-network/.env
    
    echo "✅ Request Network تنظیم شد"
fi

# راه‌اندازی مجدد کانتینرها
echo ""
echo "🐳 راه‌اندازی مجدد کانتینرها..."
if [ "$SERVER_TYPE" = "response" ]; then
    cd response-network
    sudo docker compose down
    sudo docker compose up -d --build
    cd ..
elif [ "$SERVER_TYPE" = "request" ]; then
    cd request-network  
    sudo docker compose down
    sudo docker compose up -d --build
    cd ..
fi

echo ""
echo "✅ تنظیم مجدد IP ها تکمیل شد!"
echo ""
echo "📋 مراحل بعدی:"
echo "   1. بررسی سلامت سرویس‌ها: ./test_production.sh"
if [ "$SERVER_TYPE" = "response" ]; then
    echo "   2. دسترسی به پنل: http://$RESPONSE_HOST:3000"
    echo "   3. تست API: curl http://$RESPONSE_HOST:8000/api/v1/health"
elif [ "$SERVER_TYPE" = "request" ]; then
    echo "   2. دسترسی به پنل: http://$REQUEST_HOST:3002"
    echo "   3. تست API: curl http://$REQUEST_HOST:8001/api/v1/health"
fi
echo ""
echo "🔑 اطلاعات ورود: admin / admin123456"