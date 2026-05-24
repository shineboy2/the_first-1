#!/bin/bash

# =========================================================================
# آماده‌سازی VM Template برای Export
# =========================================================================
# این اسکریپت VM را برای export به OVF آماده می‌کند
# استفاده: ./prepare_vm_template.sh [response|request]
# =========================================================================

set -e

NETWORK_TYPE="$1"

if [ "$NETWORK_TYPE" != "response" ] && [ "$NETWORK_TYPE" != "request" ]; then
    echo "استفاده: ./prepare_vm_template.sh [response|request]"
    echo ""
    echo "مثال:"
    echo "  ./prepare_vm_template.sh response    # برای Response Network VM"
    echo "  ./prepare_vm_template.sh request     # برای Request Network VM"
    exit 1
fi

echo "🚀 آماده‌سازی VM Template برای $NETWORK_TYPE Network..."
echo "================================================="

# 1. نصب dependencies مورد نیاز
echo "📦 نصب dependencies..."
sudo apt-get update
sudo apt-get install -y curl wget netcat-openbsd

# بررسی نصب Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker نصب نشده است!"
    echo "لطفاً ابتدا Docker را نصب کنید:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "sudo sh get-docker.sh"
    echo "sudo usermod -aG docker \$USER"
    exit 1
fi

# بررسی نصب Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose نصب نشده است!"
    echo "لطفاً ابتدا Docker Compose را نصب کنید:"
    echo "sudo apt-get install docker-compose-plugin"
    exit 1
fi

echo "✅ تمام dependencies موجود است"

# 2. تنظیم IP های template (localhost برای template)
echo "🔧 تنظیم IP های template..."
cat > deployment-config.env << EOF
# Template Configuration - Will be reconfigured in production
RESPONSE_HOST=localhost
RESPONSE_USER=response
RESPONSE_PASS=1

REQUEST_HOST=localhost
REQUEST_USER=request
REQUEST_PASS=1

ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_USER=response
ELASTICSEARCH_PASS=1

# FTP Server
FTP_HOST=localhost
FTP_PORT=21
FTP_USER=agftp
FTP_PASSWORD=agpass123

# API URLs (template)
REQUEST_API_URL=http://localhost:8001
RESPONSE_API_URL=http://localhost:8000

# CORS Origins (template)
REQUEST_CORS_ORIGINS=http://localhost:3002
RESPONSE_CORS_ORIGINS=http://localhost:3000
EOF

# 3. تولید فایل‌های .env template
echo "📝 تولید فایل‌های .env template..."
./generate-production-env.sh

# 4. Deploy مخصوص این network
echo "🐳 Deploy $NETWORK_TYPE Network..."
if [ "$NETWORK_TYPE" = "response" ]; then
    # Deploy Response Network (بدون Elasticsearch - به سرور خارجی متصل می‌شود)
    cd response-network
    sudo docker compose up -d --build
    cd ..
    
elif [ "$NETWORK_TYPE" = "request" ]; then
    # Deploy Request Network
    cd request-network
    sudo docker compose up -d --build
    cd ..
fi

# 5. انتظار برای آماده شدن سرویس‌ها
echo "⏳ انتظار برای آماده شدن سرویس‌ها..."
sleep 30

# 6. تست سلامت
echo "🔍 تست سلامت سرویس‌ها..."
if [ "$NETWORK_TYPE" = "response" ]; then
    # تست Response API
    for i in {1..10}; do
        if curl -s -f "http://localhost:8000/api/v1/health" > /dev/null; then
            echo "✅ Response API آماده است"
            break
        fi
        echo "انتظار برای Response API... ($i/10)"
        sleep 5
    done
    
    echo "ℹ️ Elasticsearch: به سرور خارجی متصل می‌شود (IP در .env تنظیم شده)"
    
elif [ "$NETWORK_TYPE" = "request" ]; then
    # تست Request API
    for i in {1..10}; do
        if curl -s -f "http://localhost:8001/api/v1/health" > /dev/null; then
            echo "✅ Request API آماده است"
            break
        fi
        echo "انتظار برای Request API... ($i/10)"
        sleep 5
    done
fi

# 7. آماده‌سازی برای export
echo "🧹 آماده‌سازی برای export..."

# پاک‌سازی فایل‌های موقت
sudo apt-get clean
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# پاک‌سازی history
history -c
cat /dev/null > ~/.bash_history

# پاک‌سازی لاگ‌های سیستم
sudo truncate -s 0 /var/log/*.log
sudo find /var/log -name "*.log" -exec truncate -s 0 {} \;

# 8. ایجاد فایل اطلاعات VM
cat > VM_INFO.txt << EOF
===========================================
VM Template Information
===========================================

Network Type: $NETWORK_TYPE Network
Created: $(date)
Ubuntu Version: $(lsb_release -d | cut -f2)

Services Included:
EOF

if [ "$NETWORK_TYPE" = "response" ]; then
    cat >> VM_INFO.txt << EOF
- Response Network API (Port 8000)
- Admin Panel (Port 3000)
- PostgreSQL Database
- Redis Cache
- Elasticsearch Connection (External Server)

Access URLs:
- API: http://[SERVER_IP]:8000
- Admin Panel: http://[SERVER_IP]:3000

Note: Elasticsearch runs on separate server
EOF
elif [ "$NETWORK_TYPE" = "request" ]; then
    cat >> VM_INFO.txt << EOF
- Request Network API (Port 8001)
- Admin Panel (Port 3002)
- PostgreSQL Database
- Redis Cache

Access URLs:
- API: http://[SERVER_IP]:8001
- Admin Panel: http://[SERVER_IP]:3002
EOF
fi

cat >> VM_INFO.txt << EOF

Default Login:
- Username: admin
- Password: admin123456

Post-Import Steps:
1. Run: ./reconfigure_production_ips.sh
2. Test: ./test_production.sh

===========================================
EOF

echo ""
echo "✅ VM Template آماده شد!"
echo ""
echo "📋 مراحل بعدی:"
echo "   1. VM را خاموش کنید"
echo "   2. از VMware/VirtualBox به OVF export کنید"
echo "   3. فایل OVF را به محیط پروداکشن منتقل کنید"
echo "   4. در پروداکشن import کنید"
echo "   5. اسکریپت reconfigure_production_ips.sh را اجرا کنید"
echo ""
echo "📄 فایل VM_INFO.txt حاوی اطلاعات کامل VM است"