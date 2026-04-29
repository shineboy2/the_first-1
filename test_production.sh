#!/bin/bash

# =========================================================================
# اسکریپت تست سریع سلامت سیستم در پروداکشن
# =========================================================================
# این اسکریپت سلامت تمام سرویس‌ها را بررسی می‌کند
# استفاده: ./test_production.sh
# =========================================================================

set -e

# بارگذاری تنظیمات
if [ -f "deployment-config.env" ]; then
    source deployment-config.env
    echo "✅ تنظیمات از deployment-config.env بارگذاری شد"
else
    echo "❌ فایل deployment-config.env یافت نشد!"
    exit 1
fi

echo ""
echo "🔍 شروع تست سلامت سیستم..."
echo "================================================="

# تست Elasticsearch (سرور خارجی)
echo ""
echo "🔍 تست Elasticsearch (سرور خارجی)..."
if curl -s -f "http://${ELASTICSEARCH_HOST}:9200/_cluster/health" > /dev/null; then
    HEALTH=$(curl -s "http://${ELASTICSEARCH_HOST}:9200/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$HEALTH" = "green" ] || [ "$HEALTH" = "yellow" ]; then
        echo "✅ Elasticsearch سالم است (وضعیت: $HEALTH)"
    else
        echo "⚠️ Elasticsearch مشکل دارد (وضعیت: $HEALTH)"
    fi
else
    echo "❌ Elasticsearch در دسترس نیست"
    echo "ℹ️ مطمئن شوید Elasticsearch روی $ELASTICSEARCH_HOST:9200 راه‌اندازی شده است"
fi

# تست Kibana (اگر روی همان سرور Elasticsearch باشد)
echo ""
echo "🔍 تست Kibana (اختیاری)..."
if curl -s -f "http://${ELASTICSEARCH_HOST}:5601/api/status" > /dev/null; then
    echo "✅ Kibana در دسترس است"
else
    echo "ℹ️ Kibana در دسترس نیست یا نصب نشده (اختیاری)"
fi

# تست Response Network API
echo ""
echo "🔍 تست Response Network API..."
if curl -s -f "${RESPONSE_API_URL}/api/v1/health" > /dev/null; then
    echo "✅ Response API سالم است"
else
    echo "❌ Response API در دسترس نیست"
fi

# تست Response Network Panel
echo ""
echo "🔍 تست Response Network Panel..."
RESPONSE_PANEL_URL="${RESPONSE_API_URL%:*}:3000"
if curl -s -f "$RESPONSE_PANEL_URL" > /dev/null; then
    echo "✅ Response Panel در دسترس است"
else
    echo "❌ Response Panel در دسترس نیست"
fi

# تست Request Network API
echo ""
echo "🔍 تست Request Network API..."
if curl -s -f "${REQUEST_API_URL}/api/v1/health" > /dev/null; then
    echo "✅ Request API سالم است"
else
    echo "❌ Request API در دسترس نیست"
fi

# تست Request Network Panel
echo ""
echo "🔍 تست Request Network Panel..."
REQUEST_PANEL_URL="${REQUEST_API_URL%:*}:3002"
if curl -s -f "$REQUEST_PANEL_URL" > /dev/null; then
    echo "✅ Request Panel در دسترس است"
else
    echo "❌ Request Panel در دسترس نیست"
fi

# تست اتصال بین شبکه‌ها (FTP)
echo ""
echo "🔍 تست اتصال FTP..."
if nc -z -w5 "$FTP_HOST" "${FTP_PORT:-21}" 2>/dev/null; then
    echo "✅ سرور FTP در دسترس است"
else
    echo "⚠️ سرور FTP در دسترس نیست"
fi

echo ""
echo "================================================="
echo "🎉 تست سلامت سیستم تکمیل شد!"
echo ""
echo "📋 لینک‌های مفید:"
echo "   Response Panel: $RESPONSE_PANEL_URL"
echo "   Request Panel: $REQUEST_PANEL_URL"
echo "   Elasticsearch: http://${ELASTICSEARCH_HOST}:9200 (سرور خارجی)"
if curl -s -f "http://${ELASTICSEARCH_HOST}:5601/api/status" > /dev/null; then
    echo "   Kibana: http://${ELASTICSEARCH_HOST}:5601 (اختیاری)"
fi
echo ""
echo "🔑 اطلاعات ورود پیش‌فرض:"
echo "   نام کاربری: admin"
echo "   رمز عبور: admin123456"
echo ""
echo "⚠️ توجه: رمز عبور admin را در محیط پروداکشن تغییر دهید!"