#!/bin/bash

# اسکریپت جداسازی شبکه‌ها
# این اسکریپت کدهای shared را به هر شبکه کپی می‌کند و import ها را تغییر می‌دهد

set -e  # خروج در صورت بروز خطا

echo "🚀 شروع فرآیند جداسازی شبکه‌ها..."
echo "================================================="

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# تابع نمایش پیام
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# بررسی وجود پوشه‌های ضروری
check_prerequisites() {
    echo "🔍 بررسی پیش‌نیازها..."
    
    if [ ! -d "shared" ]; then
        log_error "پوشه shared یافت نشد!"
        exit 1
    fi
    
    if [ ! -d "request-network" ]; then
        log_error "پوشه request-network یافت نشد!"
        exit 1
    fi
    
    if [ ! -d "response-network" ]; then
        log_error "پوشه response-network یافت نشد!"
        exit 1
    fi
    
    log_info "پیش‌نیازها بررسی شد"
}

# بک‌آپ گیری
create_backup() {
    echo "💾 ایجاد بک‌آپ..."
    
    BACKUP_DIR="../project-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r . "$BACKUP_DIR"
    log_info "بک‌آپ در $BACKUP_DIR ایجاد شد"
}

# کپی shared به request-network
copy_shared_to_request() {
    echo "📁 کپی shared به request-network..."
    
    # ایجاد پوشه
    mkdir -p request-network/api/shared
    
    # کپی فایل‌ها
    cp -r shared/* request-network/api/shared/
    
    # بررسی کپی
    if [ -d "request-network/api/shared" ]; then
        log_info "shared به request-network کپی شد"
        echo "   فایل‌های کپی شده: $(find request-network/api/shared -name "*.py" | wc -l) فایل Python"
    else
        log_error "خطا در کپی shared به request-network"
        exit 1
    fi
}

# کپی shared به response-network
copy_shared_to_response() {
    echo "📁 کپی shared به response-network..."
    
    # ایجاد پوشه
    mkdir -p response-network/api/shared
    
    # کپی فایل‌ها
    cp -r shared/* response-network/api/shared/
    
    # بررسی کپی
    if [ -d "response-network/api/shared" ]; then
        log_info "shared به response-network کپی شد"
        echo "   فایل‌های کپی شده: $(find response-network/api/shared -name "*.py" | wc -l) فایل Python"
    else
        log_error "خطا در کپی shared به response-network"
        exit 1
    fi
}

# تغییر import ها در request-network
fix_imports_request() {
    echo "🔧 تغییر import ها در request-network..."
    
    # تغییر from shared. به from .shared.
    find request-network/api -name "*.py" -type f -exec sed -i 's/from shared\./from .shared./g' {} \;
    
    # تغییر import shared به import .shared
    find request-network/api -name "*.py" -type f -exec sed -i 's/import shared/import .shared/g' {} \;
    
    log_info "import ها در request-network تغییر یافت"
}

# تغییر import ها در response-network
fix_imports_response() {
    echo "🔧 تغییر import ها در response-network..."
    
    # تغییر from shared. به from .shared.
    find response-network/api -name "*.py" -type f -exec sed -i 's/from shared\./from .shared./g' {} \;
    
    # تغییر import shared به import .shared
    find response-network/api -name "*.py" -type f -exec sed -i 's/import shared/import .shared/g' {} \;
    
    log_info "import ها در response-network تغییر یافت"
}

# بروزرسانی Dockerfile.request
update_dockerfile_request() {
    echo "🐳 بروزرسانی Dockerfile.request..."
    
    if [ -f "Dockerfile.request" ]; then
        # بک‌آپ فایل اصلی
        cp Dockerfile.request Dockerfile.request.backup
        
        # تغییر COPY . /app به COPY request-network/ /app/request-network/
        sed -i 's|COPY \. /app|COPY request-network/ /app/request-network/|g' Dockerfile.request
        
        # اضافه کردن exclude برای shared مرکزی اگر لازم باشد
        log_info "Dockerfile.request بروزرسانی شد"
    else
        log_warning "Dockerfile.request یافت نشد"
    fi
}

# بروزرسانی Frontend Dockerfile ها
update_frontend_dockerfiles() {
    echo "🎨 بروزرسانی Frontend Dockerfile ها..."
    
    # Request Network Frontend
    if [ -f "request-network/admin-panel/Dockerfile" ]; then
        cp request-network/admin-panel/Dockerfile request-network/admin-panel/Dockerfile.backup
        
        # ایجاد generate-config.sh
        cat > request-network/admin-panel/generate-config.sh << 'EOF'
#!/bin/bash
envsubst < /app/public/config.template.js > /app/public/config.js
EOF
        
        # ایجاد config template
        mkdir -p request-network/admin-panel/public
        echo 'window.__RUNTIME_CONFIG__={API_URL:"${NEXT_PUBLIC_API_URL}"}' > request-network/admin-panel/public/config.template.js
        
        log_info "Request Network Frontend Dockerfile آماده شد"
    fi
    
    # Response Network Frontend
    if [ -f "response-network/admin-panel/Dockerfile" ]; then
        cp response-network/admin-panel/Dockerfile response-network/admin-panel/Dockerfile.backup
        
        # ایجاد generate-config.sh
        cat > response-network/admin-panel/generate-config.sh << 'EOF'
#!/bin/bash
envsubst < /app/public/config.template.js > /app/public/config.js
EOF
        
        # ایجاد config template
        mkdir -p response-network/admin-panel/public
        echo 'window.__RUNTIME_CONFIG__={API_URL:"${NEXT_PUBLIC_API_URL}"}' > response-network/admin-panel/public/config.template.js
        
        log_info "Response Network Frontend Dockerfile آماده شد"
    fi
}

# بروزرسانی API Client ها برای Runtime Config
update_api_clients() {
    echo "🔧 بروزرسانی API Client ها..."
    
    # Request Network API Client
    if [ -f "request-network/admin-panel/app/(auth)/api.ts" ]; then
        cp request-network/admin-panel/app/(auth)/api.ts request-network/admin-panel/app/(auth)/api.ts.backup
        
        # اضافه کردن Runtime Config support
        sed -i '/baseURL: process.env.NEXT_PUBLIC_API_URL/c\
  baseURL: (typeof window !== "undefined" && window.__RUNTIME_CONFIG__) ? window.__RUNTIME_CONFIG__.API_URL : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"),' request-network/admin-panel/app/(auth)/api.ts
        
        log_info "Request Network API Client بروزرسانی شد"
    fi
    
    # Response Network API Client
    if [ -f "response-network/admin-panel/app/(auth)/api.ts" ]; then
        cp response-network/admin-panel/app/(auth)/api.ts response-network/admin-panel/app/(auth)/api.ts.backup
        
        # اضافه کردن Runtime Config support
        sed -i '/baseURL: process.env.NEXT_PUBLIC_API_URL/c\
  baseURL: (typeof window !== "undefined" && window.__RUNTIME_CONFIG__) ? window.__RUNTIME_CONFIG__.API_URL : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"),' response-network/admin-panel/app/(auth)/api.ts
        
        log_info "Response Network API Client بروزرسانی شد"
    fi
}

# تست syntax
test_syntax() {
    echo "🧪 تست syntax فایل‌ها..."
    
    # تست request-network
    echo "   تست request-network..."
    if python -m py_compile request-network/api/main.py 2>/dev/null; then
        log_info "syntax request-network صحیح است"
    else
        log_error "خطای syntax در request-network"
        return 1
    fi
    
    # تست response-network
    echo "   تست response-network..."
    if python -m py_compile response-network/api/main.py 2>/dev/null; then
        log_info "syntax response-network صحیح است"
    else
        log_error "خطای syntax در response-network"
        return 1
    fi
}

# نمایش خلاصه تغییرات
show_summary() {
    echo ""
    echo "📊 خلاصه تغییرات:"
    echo "================================================="
    echo "✅ shared کپی شده به request-network/api/shared/"
    echo "✅ shared کپی شده به response-network/api/shared/"
    echo "✅ import ها در هر دو شبکه تغییر یافت"
    echo "✅ Dockerfile ها بروزرسانی شد"
    echo "✅ Frontend Runtime Configuration اضافه شد"
    echo "✅ API Client ها برای Runtime Config بروزرسانی شد"
    echo ""
    echo "📁 فایل‌های تغییر یافته:"
    echo "   - $(find request-network/api -name "*.py" | wc -l) فایل در request-network"
    echo "   - $(find response-network/api -name "*.py" | wc -l) فایل در response-network"
    echo ""
    echo "⚠️ مراحل بعدی:"
    echo "   1. تست docker build برای هر دو شبکه (backend + frontend)"
    echo "   2. تست docker-compose up"
    echo "   3. تست Runtime Configuration در مرورگر"
    echo "   4. در صورت موفقیت: rm -rf shared"
    echo ""
}

# تابع اصلی
main() {
    echo "شروع فرآیند جداسازی شبکه‌ها در $(date)"
    echo ""
    
    # بررسی تأیید کاربر
    read -p "آیا مطمئن هستید که می‌خواهید ادامه دهید؟ (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "عملیات لغو شد"
        exit 0
    fi
    
    check_prerequisites
    create_backup
    copy_shared_to_request
    copy_shared_to_response
    fix_imports_request
    fix_imports_response
    update_dockerfile_request
    update_frontend_dockerfiles
    update_api_clients
    
    if test_syntax; then
        show_summary
        log_info "فرآیند جداسازی با موفقیت تکمیل شد!"
    else
        log_error "خطا در تست syntax. لطفاً خطاها را بررسی کنید."
        exit 1
    fi
}

# اجرای تابع اصلی
main "$@"