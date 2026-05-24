#!/bin/bash

# اسکریپت تست جداسازی شبکه‌ها
# این اسکریپت صحت جداسازی را بررسی می‌کند

set -e

echo "🧪 تست جداسازی شبکه‌ها..."
echo "================================================="

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# تست وجود shared در هر شبکه
test_shared_exists() {
    echo "📁 بررسی وجود shared در هر شبکه..."
    
    if [ -d "request-network/api/shared" ]; then
        log_info "shared در request-network موجود است"
    else
        log_error "shared در request-network موجود نیست"
        return 1
    fi
    
    if [ -d "response-network/api/shared" ]; then
        log_info "shared در response-network موجود است"
    else
        log_error "shared در response-network موجود نیست"
        return 1
    fi
}

# تست import ها
test_imports() {
    echo "🔍 بررسی import ها..."
    
    # بررسی import های قدیمی (نباید وجود داشته باشد)
    old_imports_request=$(grep -r "from shared\." request-network/api/ 2>/dev/null | wc -l || echo "0")
    old_imports_response=$(grep -r "from shared\." response-network/api/ 2>/dev/null | wc -l || echo "0")
    
    if [ "$old_imports_request" -eq 0 ]; then
        log_info "import های قدیمی در request-network پاک شده"
    else
        log_error "$old_imports_request import قدیمی در request-network باقی مانده"
        return 1
    fi
    
    if [ "$old_imports_response" -eq 0 ]; then
        log_info "import های قدیمی در response-network پاک شده"
    else
        log_error "$old_imports_response import قدیمی در response-network باقی مانده"
        return 1
    fi
    
    # بررسی import های جدید
    new_imports_request=$(grep -r "from \.shared\." request-network/api/ 2>/dev/null | wc -l || echo "0")
    new_imports_response=$(grep -r "from \.shared\." response-network/api/ 2>/dev/null | wc -l || echo "0")
    
    log_info "import های جدید در request-network: $new_imports_request"
    log_info "import های جدید در response-network: $new_imports_response"
}

# تست Docker build
test_docker_build() {
    echo "🐳 تست Docker build..."
    
    # تست request-network
    echo "   تست build request-network..."
    if docker build -f Dockerfile.request -t test-request-separation . >/dev/null 2>&1; then
        log_info "Docker build request-network موفق"
        docker rmi test-request-separation >/dev/null 2>&1 || true
    else
        log_error "Docker build request-network ناموفق"
        return 1
    fi
    
    # تست response-network
    echo "   تست build response-network..."
    if docker build -f Dockerfile.response -t test-response-separation . >/dev/null 2>&1; then
        log_info "Docker build response-network موفق"
        docker rmi test-response-separation >/dev/null 2>&1 || true
    else
        log_error "Docker build response-network ناموفق"
        return 1
    fi
}

# تست syntax Python
test_python_syntax() {
    echo "🐍 تست syntax Python..."
    
    # تست request-network
    if python -m py_compile request-network/api/main.py 2>/dev/null; then
        log_info "syntax request-network/api/main.py صحیح"
    else
        log_error "خطای syntax در request-network/api/main.py"
        return 1
    fi
    
    # تست response-network
    if python -m py_compile response-network/api/main.py 2>/dev/null; then
        log_info "syntax response-network/api/main.py صحیح"
    else
        log_error "خطای syntax در response-network/api/main.py"
        return 1
    fi
}

# بررسی حجم فایل‌ها
check_file_sizes() {
    echo "📊 بررسی حجم فایل‌ها..."
    
    request_shared_size=$(du -sh request-network/api/shared 2>/dev/null | cut -f1 || echo "N/A")
    response_shared_size=$(du -sh response-network/api/shared 2>/dev/null | cut -f1 || echo "N/A")
    
    echo "   حجم shared در request-network: $request_shared_size"
    echo "   حجم shared در response-network: $response_shared_size"
    
    request_files=$(find request-network/api/shared -name "*.py" | wc -l 2>/dev/null || echo "0")
    response_files=$(find response-network/api/shared -name "*.py" | wc -l 2>/dev/null || echo "0")
    
    echo "   تعداد فایل‌های Python در request-network/shared: $request_files"
    echo "   تعداد فایل‌های Python در response-network/shared: $response_files"
}

# نمایش گزارش نهایی
show_report() {
    echo ""
    echo "📋 گزارش نهایی تست جداسازی:"
    echo "================================================="
    
    if test_shared_exists && test_imports && test_python_syntax; then
        log_info "همه تست‌ها موفق بود!"
        echo ""
        echo "✅ جداسازی شبکه‌ها با موفقیت انجام شد"
        echo "✅ هر شبکه shared مخصوص خود را دارد"
        echo "✅ import ها صحیح تغییر یافته‌اند"
        echo "✅ syntax فایل‌ها صحیح است"
        echo ""
        echo "🎯 مراحل بعدی:"
        echo "   1. تست Docker build: ./test_separation.sh --docker"
        echo "   2. تست docker-compose up"
        echo "   3. تست API endpoints"
        echo "   4. در صورت موفقیت کامل: rm -rf shared"
        return 0
    else
        log_error "برخی تست‌ها ناموفق بود!"
        echo ""
        echo "❌ لطفاً خطاها را بررسی و رفع کنید"
        return 1
    fi
}

# تابع اصلی
main() {
    if [ "$1" == "--docker" ]; then
        echo "🐳 اجرای تست‌های Docker..."
        test_docker_build
    else
        test_shared_exists
        test_imports
        test_python_syntax
        check_file_sizes
        show_report
    fi
}

main "$@"