#!/bin/bash
# reconfigure_request_production.sh
# اسکریپت تغییر IP برای Request Network در محیط پروداکشن

set -e

NEW_IP="$1"
FTP_IP="$2"
GATEWAY="$3"

if [ -z "$NEW_IP" ] || [ -z "$FTP_IP" ]; then
    echo "❌ خطا: پارامترهای کافی وارد نشده"
    echo ""
    echo "استفاده:"
    echo "  $0 <NEW_REQUEST_IP> <FTP_IP> [GATEWAY]"
    echo ""
    echo "مثال:"
    echo "  $0 10.0.1.100 10.0.1.50 10.0.1.1"
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "🔧 تنظیم مجدد Request Network برای محیط پروداکشن"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 IP جدید: $NEW_IP"
echo "📍 FTP Server: $FTP_IP"
if [ -n "$GATEWAY" ]; then
    echo "📍 Gateway: $GATEWAY"
fi
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

cd ~/request-network

# Backup فایل .env
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup از .env گرفته شد"
fi

# به‌روزرسانی .env
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${NEW_IP}:8001|g" .env
sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=http://localhost:3002,http://${NEW_IP}:3002|g" .env
sed -i "s|FTP_HOST=.*|FTP_HOST=${FTP_IP}|g" .env

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
echo "✅ تنظیمات Request Network با موفقیت انجام شد!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 آدرس‌های جدید:"
echo "   🌐 Admin Panel: http://${NEW_IP}:3002"
echo "   🔌 API: http://${NEW_IP}:8001"
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
if curl -s -f "http://localhost:8001/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API سالم است"
else
    echo "⚠️  API هنوز آماده نیست. لطفاً چند لحظه صبر کنید."
fi

echo ""
echo "💡 نکته: برای تغییر IP سیستم عامل از دستور زیر استفاده کنید:"
echo "   sudo nano /etc/netplan/00-installer-config.yaml"
echo ""
