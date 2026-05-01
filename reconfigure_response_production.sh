#!/bin/bash
# reconfigure_response_production.sh
# اسکریپت تغییر IP برای Response Network در محیط پروداکشن

set -e

NEW_IP="$1"
FTP_IP="$2"
ES_IP="$3"

if [ -z "$NEW_IP" ] || [ -z "$FTP_IP" ] || [ -z "$ES_IP" ]; then
    echo "❌ خطا: پارامترهای کافی وارد نشده"
    echo ""
    echo "استفاده:"
    echo "  $0 <NEW_RESPONSE_IP> <FTP_IP> <ELASTICSEARCH_IP>"
    echo ""
    echo "مثال:"
    echo "  $0 10.0.2.100 10.0.1.50 10.0.2.50"
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "🔧 تنظیم مجدد Response Network برای محیط پروداکشن"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 IP جدید: $NEW_IP"
echo "📍 FTP Server: $FTP_IP"
echo "📍 Elasticsearch: $ES_IP"
echo ""

# تایید از کاربر
read -p "آیا از ادامه عملیات اطمینان دارید؟ (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ عملیات لغو شد"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 مرحله 1: به‌روزرسانی فایل .env"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ~/response-network

# Backup فایل .env
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup از .env گرفته شد"
fi

# به‌روزرسانی .env
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${NEW_IP}:8000|g" .env
sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:3000,http://${NEW_IP}:3000|g" .env
sed -i "s|FTP_HOST=.*|FTP_HOST=${FTP_IP}|g" .env

# اضافه یا به‌روزرسانی ELASTICSEARCH_URL
if grep -q "ELASTICSEARCH_URL=" .env; then
    sed -i "s|ELASTICSEARCH_URL=.*|ELASTICSEARCH_URL=http://${ES_IP}:9200|g" .env
else
    echo "ELASTICSEARCH_URL=http://${ES_IP}:9200" >> .env
fi

echo "✅ فایل .env به‌روز شد"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 مرحله 2: Restart کانتینرها"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose down
echo "⏸️  کانتینرها متوقف شدند"

docker compose up -d
echo "▶️  کانتینرها شروع شدند"
echo ""

echo "⏳ صبر برای آماده شدن سرویس‌ها..."
sleep 15

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 مرحله 3: بررسی وضعیت"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose ps

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ تنظیمات Response Network با موفقیت انجام شد!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 آدرس‌های جدید:"
echo "   🌐 Admin Panel: http://${NEW_IP}:3000"
echo "   🔌 API: http://${NEW_IP}:8000"
echo "   🌺 Flower: http://${NEW_IP}:5555"
echo ""
echo "🔐 اطلاعات ورود:"
echo "   Username: admin"
echo "   Password: admin123456"
echo ""
echo "⚠️  توجه: حتماً رمز عبور را تغییر دهید!"
echo ""

# تست سلامت API
echo "🔍 تست سلامت API..."
if curl -s -f "http://localhost:8000/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API سالم است"
else
    echo "⚠️  API هنوز آماده نیست. لطفاً چند لحظه صبر کنید."
fi

# تست ارتباط با Elasticsearch
echo "🔍 تست ارتباط با Elasticsearch..."
if curl -s -f "http://${ES_IP}:9200" > /dev/null 2>&1; then
    echo "✅ Elasticsearch در دسترس است"
else
    echo "⚠️  Elasticsearch در دسترس نیست. لطفاً IP را بررسی کنید."
fi

echo ""
echo "💡 نکته: برای تغییر IP سیستم عامل از دستور زیر استفاده کنید:"
echo "   sudo nano /etc/netplan/00-installer-config.yaml"
echo ""
