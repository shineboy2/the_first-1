#!/bin/bash

# =========================================================================
# Production Deployment Script for Request & Response Networks
# =========================================================================
# این اسکریپت برای استقرار در محیط پروداکشن طراحی شده است
# قبل از اجرا، فایل deployment-config.env را با IP های پروداکشن تنظیم کنید
# =========================================================================

set -e  # Exit on any error

# بارگذاری تنظیمات deployment
if [ -f "deployment-config.env" ]; then
    source deployment-config.env
    echo "✅ تنظیمات deployment از deployment-config.env بارگذاری شد"
else
    echo "❌ فایل deployment-config.env یافت نشد!"
    echo "لطفاً ابتدا فایل deployment-config.env را با IP های پروداکشن ایجاد کنید."
    exit 1
fi

# بررسی وجود متغیرهای ضروری
required_vars=("RESPONSE_HOST" "REQUEST_HOST" "ELASTICSEARCH_HOST" "FTP_HOST")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ متغیر $var در deployment-config.env تعریف نشده است"
        exit 1
    fi
done

deploy_elasticsearch() {
    local HOST=$ELASTICSEARCH_HOST
    local USER=${ELASTICSEARCH_USER:-response}
    local PASS=${ELASTICSEARCH_PASS:-1}
    local TARGET_DIR="~/elasticsearch"
    
    echo -e "\n================================================="
    echo "🔍 استقرار Elasticsearch روی $HOST..."
    echo "================================================="
    
    # 1. ایجاد پوشه هدف
    echo "📁 ایجاد پوشه هدف..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} "mkdir -p ${TARGET_DIR}"
    
    # 2. کپی فایل docker-compose.elasticsearch.yml
    echo "🔄 کپی تنظیمات Elasticsearch..."
    sshpass -p "$PASS" scp -o "StrictHostKeyChecking=no" \
        ./docker-compose.elasticsearch.yml ${USER}@${HOST}:${TARGET_DIR}/docker-compose.yml
    
    # 3. راه‌اندازی Elasticsearch
    echo "🐳 راه‌اندازی Elasticsearch..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
        "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose up --build -d"
    
    # 4. انتظار برای آماده شدن Elasticsearch
    echo "⏳ انتظار برای آماده شدن Elasticsearch..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "تلاش $attempt/$max_attempts: بررسی سلامت Elasticsearch..."
        
        if sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} \
            "curl -s http://localhost:9200/_cluster/health" > /dev/null 2>&1; then
            echo "✅ Elasticsearch آماده است!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ Elasticsearch پس از $max_attempts تلاش راه‌اندازی نشد"
            return 1
        fi
        
        sleep 5
        ((attempt++))
    done
    
    echo "✅ استقرار Elasticsearch تکمیل شد!"
    echo "ℹ️ توجه: Response Network باید به این سرور متصل شود"
}

deploy_network() {
    local NETWORK=$1
    local HOST=$2
    local USER=$3
    local PASS=$4
    local TARGET_DIR="~/${NETWORK}"
    
    echo -e "\n================================================="
    echo "🚀 استقرار $NETWORK روی $HOST..."
    echo "================================================="
    
    # 1. ایجاد پوشه هدف در سرور
    echo "📁 ایجاد پوشه هدف در سرور..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} "mkdir -p ${TARGET_DIR}"

    # 2. همگام‌سازی فایل‌ها با rsync
    echo "🔄 همگام‌سازی فایل‌ها با rsync..."
    sshpass -p "$PASS" rsync -avz --delete \
        --exclude="node_modules" \
        --exclude=".next" \
        --exclude="venv" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="shared_data" \
        --exclude="postgres_data" \
        --exclude="redis_data" \
        --exclude="*.log" \
        --exclude=".pytest_cache" \
        --exclude="*.pyc" \
        --exclude="deployment-config.env" \
        ./${NETWORK}/ ${USER}@${HOST}:${TARGET_DIR}/

    # 3. بازراه‌اندازی کانتینرهای Docker
    if [ "$RESET_DB" == "true" ]; then
        echo "🗑️ پاک‌سازی volumes برای reset دیتابیس..."
        sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
            "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose -p ${NETWORK} down -v"
    fi
    
    echo "🐳 بازسازی و راه‌اندازی مجدد کانتینرهای Docker..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
        "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose -p ${NETWORK} up --build -d"
        
    # 4. راه‌اندازی اولیه (برای استقرارهای جدید)
    if [ "$INIT_DB" == "true" ]; then
        echo "⚙️ اجرای اسکریپت‌های راه‌اندازی اولیه برای $NETWORK..."
        sleep 10  # انتظار برای آماده شدن دیتابیس
        
        if [ "$NETWORK" == "request-network" ]; then
            echo "🔧 راه‌اندازی دیتابیس Request Network..."
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec request-api alembic upgrade head"
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec request-api python init_db.py"
        elif [ "$NETWORK" == "response-network" ]; then
            echo "🔧 راه‌اندازی دیتابیس Response Network..."
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec response-api python manage.py migrate"
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec response-api python create_admin.py"
        fi
        echo "✅ اسکریپت‌های راه‌اندازی تکمیل شد."
    fi

    echo "✅ استقرار $NETWORK با موفقیت تکمیل شد!"
}

# پردازش پارامترهای ورودی
INIT_DB="false"
RESET_DB="false"
TARGET_NET="$1"

if [ "$2" == "--init" ] || [ "$3" == "--init" ]; then
    INIT_DB="true"
    echo "⚙️ فلگ راه‌اندازی اولیه تشخیص داده شد - اسکریپت‌های setup اجرا خواهند شد."
fi

if [ "$2" == "--reset-db" ] || [ "$3" == "--reset-db" ]; then
    RESET_DB="true"
    echo "🔄 فلگ reset دیتابیس تشخیص داده شد - volumes قبل از استقرار پاک خواهند شد."
fi

# اجرای استقرار بر اساس پارامتر ورودی
case "$TARGET_NET" in
    "response")
        deploy_network "response-network" "$RESPONSE_HOST" "${RESPONSE_USER:-response}" "${RESPONSE_PASS:-1}"
        echo "ℹ️ توجه: Response Network به Elasticsearch خارجی متصل می‌شود"
        echo "   مطمئن شوید Elasticsearch روی $ELASTICSEARCH_HOST:9200 در دسترس است"
        ;;
    "request")
        deploy_network "request-network" "$REQUEST_HOST" "${REQUEST_USER:-request}" "${REQUEST_PASS:-1}"
        ;;
    "elasticsearch")
        deploy_elasticsearch
        ;;
    "all")
        deploy_elasticsearch
        deploy_network "response-network" "$RESPONSE_HOST" "${RESPONSE_USER:-response}" "${RESPONSE_PASS:-1}"
        deploy_network "request-network" "$REQUEST_HOST" "${REQUEST_USER:-request}" "${REQUEST_PASS:-1}"
        echo "ℹ️ توجه: Response Network به Elasticsearch خارجی متصل شده است"
        ;;
    *)
        echo "استفاده: ./deploy_production.sh [response | request | elasticsearch | all] [--init] [--reset-db]"
        echo ""
        echo "مثال‌ها:"
        echo "  ./deploy_production.sh elasticsearch               # فقط Elasticsearch (سرور جداگانه)"
        echo "  ./deploy_production.sh response                    # فقط Response Network"
        echo "  ./deploy_production.sh request                     # فقط Request Network"
        echo "  ./deploy_production.sh all --init --reset-db       # همه (Elasticsearch + Networks)"
        echo ""
        echo "⚠️ توجه:"
        echo "   - Elasticsearch روی سرور جداگانه نصب می‌شود"
        echo "   - Response Network به Elasticsearch خارجی متصل می‌شود"
        echo "   - قبل از اجرا، فایل deployment-config.env را تنظیم کنید"
        exit 1
        ;;
esac

echo ""
echo "🎉 استقرار production تکمیل شد!"
echo "📋 مراحل بعدی:"
echo "   1. بررسی سلامت سرویس‌ها"
echo "   2. تست عملکرد API ها"
echo "   3. بررسی لاگ‌ها در صورت بروز مشکل"