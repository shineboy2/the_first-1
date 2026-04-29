#!/bin/bash

# =========================================================================
# تغییر IP های سرویس‌ها - اجرا مستقیم روی سرور
# =========================================================================
# این اسکریپت را مستقیم روی سرور اجرا کنید:
#   cd ~/project/response-network  (یا request-network)
#   ./change_ip.sh
# =========================================================================

set -e

# تشخیص خودکار نوع سرور
if [ -f "docker-compose.yml" ]; then
    if grep -q "response-api\|response-db" docker-compose.yml 2>/dev/null; then
        SERVER_TYPE="response"
    elif grep -q "request-api\|request-db" docker-compose.yml 2>/dev/null; then
        SERVER_TYPE="request"
    else
        echo "❌ نوع سرور تشخیص داده نشد!"
        exit 1
    fi
else
    echo "❌ این اسکریپت باید داخل پوشه response-network یا request-network اجرا شود"
    exit 1
fi

echo "🔍 سرور تشخیص داده شده: $SERVER_TYPE Network"
echo "================================================="

# اگر فایل ip_config.env وجود داشت، از آن بخوان
if [ -f "ip_config.env" ]; then
    echo "📄 بارگذاری IP ها از فایل ip_config.env..."
    source ip_config.env
    echo "   MY_IP=$MY_IP"
    [ -n "$ES_IP" ] && echo "   ES_IP=$ES_IP"
    echo "   FTP_IP=$FTP_IP"
    echo ""
else
    # دریافت دستی IP ها
    echo "💡 نکته: می‌توانید فایل ip_config.env بسازید تا IP ها را از آن بخواند"
    echo ""

    # نمایش لیست IP های موجود
    echo "📡 IP های موجود روی این سرور:"
    ip -4 addr show | grep inet | awk '{print "   " $NF ": " $2}' | grep -v "127.0.0.1"
    echo ""

    read -p "IP این سرور: " MY_IP

    if [ "$SERVER_TYPE" = "response" ]; then
        read -p "IP سرور Elasticsearch: " ES_IP
        read -p "IP سرور FTP: " FTP_IP
        FTP_IP=${FTP_IP:-$ES_IP}
    elif [ "$SERVER_TYPE" = "request" ]; then
        read -p "IP سرور FTP (Response Network): " FTP_IP
    fi
fi

if [ "$SERVER_TYPE" = "response" ]; then

    echo ""
    echo "📋 تنظیمات جدید:"
    echo "   Response API: http://$MY_IP:8000"
    echo "   Admin Panel:  http://$MY_IP:3000"
    echo "   Elasticsearch: http://$ES_IP:9200"
    echo "   FTP: $FTP_IP"

elif [ "$SERVER_TYPE" = "request" ]; then
    read -p "IP سرور FTP (Response Network): " FTP_IP

    echo ""
    echo "📋 تنظیمات جدید:"
    echo "   Request API:  http://$MY_IP:8001"
    echo "   Admin Panel:  http://$MY_IP:3002"
    echo "   FTP: $FTP_IP"
fi

echo ""
read -p "تأیید می‌کنید؟ (y/n): " confirm
[ "$confirm" != "y" ] && [ "$confirm" != "Y" ] && echo "لغو شد" && exit 0

# بروزرسانی فایل .env
echo ""
echo "📝 بروزرسانی فایل .env..."

if [ "$SERVER_TYPE" = "response" ]; then
    sed -i "s|FTP_HOST=.*|FTP_HOST=$FTP_IP|g" .env
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$MY_IP:8000|g" .env
    sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=[\"http://localhost:3000\",\"http://$MY_IP:3000\"]|g" .env

    # بروزرسانی ELASTICSEARCH_URL در docker-compose
    sed -i "s|ELASTICSEARCH_URL=http://[^:]*:9200|ELASTICSEARCH_URL=http://$ES_IP:9200|g" docker-compose.yml

elif [ "$SERVER_TYPE" = "request" ]; then
    sed -i "s|FTP_HOST=.*|FTP_HOST=$FTP_IP|g" .env
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$MY_IP:8001|g" .env
    sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:3002,http://$MY_IP:3002|g" .env
fi

# ری‌استارت سرویس‌ها
echo "🔄 ری‌استارت سرویس‌ها..."
sudo docker compose down
sudo docker compose up -d --build

echo ""
echo "✅ تنظیمات اعمال شد!"
echo ""
if [ "$SERVER_TYPE" = "response" ]; then
    echo "🌐 API:         http://$MY_IP:8000/api/v1/health"
    echo "🖥️  Admin Panel: http://$MY_IP:3000"
elif [ "$SERVER_TYPE" = "request" ]; then
    echo "🌐 API:         http://$MY_IP:8001/api/v1/health"
    echo "🖥️  Admin Panel: http://$MY_IP:3002"
fi