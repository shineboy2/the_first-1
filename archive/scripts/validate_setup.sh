#!/bin/bash
# Setup validation script
# Validates the complete project setup

set -e

echo "🔍 Starting project setup validation..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

check_command() {
    local cmd=$1
    local name=$2
    if command -v "$cmd" &> /dev/null; then
        version=$($cmd --version 2>&1 | head -n1)
        echo -e "${GREEN}✓${NC} $name: $version"
    else
        echo -e "${RED}✗${NC} $name: NOT FOUND"
        ((ERRORS++))
    fi
}

check_file() {
    local file=$1
    local name=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $name"
    else
        echo -e "${RED}✗${NC} $name: NOT FOUND at $file"
        ((ERRORS++))
    fi
}

check_dir() {
    local dir=$1
    local name=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $name"
    else
        echo -e "${RED}✗${NC} $name: NOT FOUND at $dir"
        ((ERRORS++))
    fi
}

# Check dependencies
echo "📦 Checking system dependencies..."
check_command "docker" "Docker"
check_command "docker-compose" "Docker Compose"
check_command "python" "Python"
check_command "git" "Git"
echo ""

# Check project structure
echo "📁 Checking project structure..."
check_dir "response-network" "Response Network"
check_dir "response-network/api" "Response Network API"
check_dir "response-network/api/workers" "Response Network Workers"
check_dir "response-network/api/models" "Response Network Models"
check_dir "request-network" "Request Network"
check_dir "request-network/api" "Request Network API"
check_dir "request-network/api/models" "Request Network Models"
check_dir "shared" "Shared Code"
check_dir "core" "Core Configuration"
echo ""

# Check configuration files
echo "⚙️  Checking configuration files..."
check_file "pyproject.toml" "pyproject.toml"
check_file "conftest.py" "conftest.py"
check_file "requirements.txt" "requirements.txt"
check_file "Dockerfile" "Dockerfile"
check_file "Dockerfile.worker" "Dockerfile.worker"
check_file "Dockerfile.beat" "Dockerfile.beat"
check_file "Dockerfile.request" "Dockerfile.request"
check_file "docker-compose.yml" "docker-compose.yml"
check_file "docker-compose.dev.yml" "docker-compose.dev.yml"
echo ""

# Check management scripts
echo "🛠️  Checking management scripts..."
check_file "response-network/api/manage.py" "Response Network manage.py"
check_file "request-network/api/manage.py" "Request Network manage.py"
check_file "entrypoint.sh" "Response Network entrypoint"
check_file "entrypoint-request.sh" "Request Network entrypoint"
echo ""

# Check documentation
echo "📖 Checking documentation..."
check_file "ARCHITECTURE.md" "Architecture documentation"
check_file "SETUP_GUIDE.md" "Setup guide"
check_file "README.md" "README"
echo ""

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set up environment variables: cp .env.example .env"
    echo "2. Start services: docker-compose up -d"
    echo "3. Check logs: docker-compose logs -f api"
    exit 0
else
    echo -e "${RED}✗ $ERRORS checks failed${NC}"
    exit 1
fi
