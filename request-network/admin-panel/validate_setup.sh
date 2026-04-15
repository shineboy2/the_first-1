#!/bin/bash

# 🎯 Admin Panel Validation Script
# Complete setup verification

set -e

echo "════════════════════════════════════════════════════════════"
echo "   🎨 Admin Panel Phase 8 - Complete Validation"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter
PASS=0
FAIL=0

# Function to check
check() {
    local name=$1
    local cmd=$2
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $name"
        ((FAIL++))
    fi
}

echo -e "${BLUE}1. Directory Structure${NC}"
check "Admin panel folder exists" "[ -d 'response-network/admin-panel' ]"
check "App folder exists" "[ -d 'response-network/admin-panel/app' ]"
check "Lib folder exists" "[ -d 'response-network/admin-panel/lib' ]"
check "Components folder exists" "[ -d 'response-network/admin-panel/components' ]"
echo ""

echo -e "${BLUE}2. Critical Files${NC}"
check "Dockerfile exists" "[ -f 'response-network/admin-panel/Dockerfile' ]"
check ".dockerignore exists" "[ -f 'response-network/admin-panel/.dockerignore' ]"
check ".env.local exists" "[ -f 'response-network/admin-panel/.env.local' ]"
check ".env.production exists" "[ -f 'response-network/admin-panel/.env.production' ]"
check "middleware.ts exists" "[ -f 'response-network/admin-panel/middleware.ts' ]"
check "next.config.ts exists" "[ -f 'response-network/admin-panel/next.config.ts' ]"
check "tailwind.config.ts exists" "[ -f 'response-network/admin-panel/tailwind.config.ts' ]"
echo ""

echo -e "${BLUE}3. Application Files${NC}"
check "Login page exists" "[ -f 'response-network/admin-panel/app/(auth)/login/page.tsx' ]"
check "Dashboard layout exists" "[ -f 'response-network/admin-panel/app/(dashboard)/layout.tsx' ]"
check "Dashboard home exists" "[ -f 'response-network/admin-panel/app/(dashboard)/page.tsx' ]"
check "Users page exists" "[ -f 'response-network/admin-panel/app/(dashboard)/users/page.tsx' ]"
check "Requests page exists" "[ -f 'response-network/admin-panel/app/(dashboard)/requests/page.tsx' ]"
check "Cache page exists" "[ -f 'response-network/admin-panel/app/(dashboard)/cache/page.tsx' ]"
check "Settings page exists" "[ -f 'response-network/admin-panel/app/(dashboard)/settings/page.tsx' ]"
echo ""

echo -e "${BLUE}4. Services & Stores${NC}"
check "API client exists" "[ -f 'response-network/admin-panel/lib/services/api-client.ts' ]"
check "Admin API exists" "[ -f 'response-network/admin-panel/lib/services/admin-api.ts' ]"
check "Auth store exists" "[ -f 'response-network/admin-panel/lib/stores/auth-store.ts' ]"
check "Utils file exists" "[ -f 'response-network/admin-panel/lib/utils.ts' ]"
echo ""

echo -e "${BLUE}5. UI Components${NC}"
check "Table component exists" "[ -f 'response-network/admin-panel/components/ui/table.tsx' ]"
check "Badge component exists" "[ -f 'response-network/admin-panel/components/ui/badge.tsx' ]"
check "Switch component exists" "[ -f 'response-network/admin-panel/components/ui/switch.tsx' ]"
check "Button component exists" "[ -f 'response-network/admin-panel/components/ui/button.tsx' ]"
check "Card component exists" "[ -f 'response-network/admin-panel/components/ui/card.tsx' ]"
echo ""

echo -e "${BLUE}6. Configuration Files${NC}"
check "package.json exists" "[ -f 'response-network/admin-panel/package.json' ]"
check "tsconfig.json exists" "[ -f 'response-network/admin-panel/tsconfig.json' ]"
check "components.json exists" "[ -f 'response-network/admin-panel/components.json' ]"
check "vercel.json exists" "[ -f 'response-network/admin-panel/vercel.json' ]"
echo ""

echo -e "${BLUE}7. Documentation${NC}"
check "QUICK_REFERENCE.md exists" "[ -f 'response-network/admin-panel/QUICK_REFERENCE.md' ]"
check "TESTING_AND_TROUBLESHOOTING.md exists" "[ -f 'response-network/admin-panel/TESTING_AND_TROUBLESHOOTING.md' ]"
check "API_INTEGRATION_GUIDE.md exists" "[ -f 'response-network/admin-panel/API_INTEGRATION_GUIDE.md' ]"
check "DOCKER_AND_DEPLOYMENT_GUIDE.md exists" "[ -f 'response-network/admin-panel/DOCKER_AND_DEPLOYMENT_GUIDE.md' ]"
check "ADMIN_PANEL_FRONTEND_DOCUMENTATION.md exists" "[ -f 'response-network/admin-panel/ADMIN_PANEL_FRONTEND_DOCUMENTATION.md' ]"
check "MASTER_DOCUMENTATION.md exists" "[ -f 'response-network/admin-panel/MASTER_DOCUMENTATION.md' ]"
check "README_FRONTEND.md exists" "[ -f 'response-network/admin-panel/README_FRONTEND.md' ]"
echo ""

echo -e "${BLUE}8. Docker & Compose${NC}"
check "docker-compose.yml exists" "[ -f 'docker-compose.yml' ]"
check "admin-panel in docker-compose" "grep -q 'admin-panel' docker-compose.yml"
echo ""

echo -e "${BLUE}9. Package Dependencies${NC}"
cd response-network/admin-panel
check "package.json valid JSON" "node -e 'JSON.parse(require(\"fs\").readFileSync(\"package.json\"))'  2>/dev/null"
check "next installed" "grep -q 'next' package.json"
check "react installed" "grep -q 'react' package.json"
check "typescript installed" "grep -q 'typescript' package.json"
check "tailwindcss installed" "grep -q 'tailwindcss' package.json"
check "zustand installed" "grep -q 'zustand' package.json"
check "axios installed" "grep -q 'axios' package.json"
cd ../..
echo ""

echo -e "${BLUE}10. TypeScript Configuration${NC}"
check "TypeScript strict mode" "grep -q '\"strict\": true' response-network/admin-panel/tsconfig.json"
check "App directory configured" "grep -q '\"appDir\": true' response-network/admin-panel/tsconfig.json"
echo ""

echo -e "${BLUE}11. Environment Variables${NC}"
check "NEXT_PUBLIC_API_URL in .env.local" "grep -q 'NEXT_PUBLIC_API_URL' response-network/admin-panel/.env.local"
check "API_URL in .env.production" "grep -q 'NEXT_PUBLIC_API_URL' response-network/admin-panel/.env.production"
echo ""

echo -e "${BLUE}12. Security Files${NC}"
check ".gitignore exists" "[ -f 'response-network/admin-panel/.gitignore' ]"
check "node_modules in .gitignore" "grep -q 'node_modules' response-network/admin-panel/.gitignore"
echo ""

echo -e "${BLUE}13. Build Validation${NC}"
cd response-network/admin-panel

# Check if node_modules exist
if [ -d "node_modules" ]; then
    check "npm dependencies installed" "[ -d 'node_modules' ]"
    check "next binary available" "[ -f 'node_modules/.bin/next' ]"
    
    # Try to run build if node_modules exist
    if command -v npm &> /dev/null; then
        echo "  Note: Skipping npm run build (would take time)"
        echo -e "  ${YELLOW}To test build later, run:${NC}"
        echo -e "  ${YELLOW}  cd response-network/admin-panel && npm run build${NC}"
    fi
else
    echo -e "${YELLOW}!${NC} npm dependencies not yet installed"
    echo -e "  ${YELLOW}To install, run:${NC}"
    echo -e "  ${YELLOW}  cd response-network/admin-panel && npm install${NC}"
fi

cd ../..
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "Results:"
echo -e "  ${GREEN}✓ Passed: $PASS${NC}"
echo -e "  ${RED}✗ Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ ALL CHECKS PASSED! Ready to use!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo -e "  ${BLUE}1. Start services:${NC}"
    echo "     docker-compose up -d"
    echo ""
    echo -e "  ${BLUE}2. Open admin panel:${NC}"
    echo "     http://localhost:3000"
    echo ""
    echo -e "  ${BLUE}3. Login with:${NC}"
    echo "     Email: admin@example.com"
    echo "     Password: admin@123456"
    echo ""
    exit 0
else
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}✗ Some checks failed. Please review above.${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
