#!/bin/bash

# Script to deploy Elasticsearch SSL fix to production
# Usage: ./deploy_elasticsearch_fix.sh [method]
# Methods: volume, rebuild, docker-cp

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.response.yml"
WORKER_CONTAINER="celery-worker-response"
BEAT_CONTAINER="celery-beat-response"
API_CONTAINER="api-response"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if docker-compose file exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    print_info "Found docker-compose file: $COMPOSE_FILE"
}

# Function to check if containers are running
check_containers() {
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "$WORKER_CONTAINER"; then
        print_error "Worker container not found: $WORKER_CONTAINER"
        exit 1
    fi
    print_info "Containers are running"
}

# Function to create backup
create_backup() {
    print_info "Creating backup..."
    BACKUP_FILE="/tmp/backup-workers-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    docker-compose -f "$COMPOSE_FILE" exec -T "$WORKER_CONTAINER" \
        tar czf "$BACKUP_FILE" /app/workers/ 2>/dev/null || true
    
    print_info "Backup created (if possible): $BACKUP_FILE"
}

# Method 1: Volume-based deployment (fastest)
deploy_volume() {
    print_info "Deploying using volume method..."
    
    # Check if files exist
    if [ ! -f "response-network/api/workers/tasks/execute_query.py" ]; then
        print_error "File not found: response-network/api/workers/tasks/execute_query.py"
        exit 1
    fi
    
    if [ ! -f "response-network/api/workers/elasticsearch_client.py" ]; then
        print_error "File not found: response-network/api/workers/elasticsearch_client.py"
        exit 1
    fi
    
    print_info "Files are in place (using volume mount)"
    
    # Restart workers
    print_info "Restarting workers..."
    docker-compose -f "$COMPOSE_FILE" restart "$WORKER_CONTAINER" "$BEAT_CONTAINER"
    
    print_info "Deployment complete!"
}

# Method 2: Rebuild images (recommended for production)
deploy_rebuild() {
    print_info "Deploying using rebuild method..."
    
    # Pull latest code
    print_info "Pulling latest code from git..."
    if git pull origin main; then
        print_info "Code updated successfully"
    else
        print_warning "Git pull failed or no changes"
    fi
    
    # Rebuild images
    print_info "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build "$WORKER_CONTAINER" "$BEAT_CONTAINER"
    
    # Recreate containers
    print_info "Recreating containers..."
    docker-compose -f "$COMPOSE_FILE" up -d --force-recreate "$WORKER_CONTAINER" "$BEAT_CONTAINER"
    
    print_info "Deployment complete!"
}

# Method 3: Docker cp (for quick testing)
deploy_docker_cp() {
    print_info "Deploying using docker cp method..."
    print_warning "This is temporary and will be lost on container restart!"
    
    # Copy files to container
    print_info "Copying files to container..."
    docker cp response-network/api/workers/tasks/execute_query.py "$WORKER_CONTAINER:/app/workers/tasks/"
    docker cp response-network/api/workers/elasticsearch_client.py "$WORKER_CONTAINER:/app/workers/"
    
    # Restart workers
    print_info "Restarting workers..."
    docker-compose -f "$COMPOSE_FILE" restart "$WORKER_CONTAINER" "$BEAT_CONTAINER"
    
    print_info "Deployment complete!"
}

# Function to verify deployment
verify_deployment() {
    print_info "Verifying deployment..."
    
    # Wait a bit for containers to start
    sleep 5
    
    # Check if containers are running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$WORKER_CONTAINER.*Up"; then
        print_info "✓ Worker container is running"
    else
        print_error "✗ Worker container is not running"
        return 1
    fi
    
    # Check logs for SSL messages
    print_info "Checking logs for SSL verification messages..."
    if docker-compose -f "$COMPOSE_FILE" logs --tail=50 "$WORKER_CONTAINER" | grep -q "ELASTICSEARCH"; then
        print_info "✓ Found Elasticsearch logs"
        docker-compose -f "$COMPOSE_FILE" logs --tail=10 "$WORKER_CONTAINER" | grep "ELASTICSEARCH"
    else
        print_warning "No Elasticsearch logs found yet (this is normal if no queries have been executed)"
    fi
    
    print_info "Verification complete!"
}

# Function to show logs
show_logs() {
    print_info "Showing worker logs (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" logs -f "$WORKER_CONTAINER"
}

# Main script
main() {
    echo "================================================"
    echo "  Elasticsearch SSL Fix Deployment Script"
    echo "================================================"
    echo ""
    
    # Parse arguments
    METHOD=${1:-rebuild}
    
    # Validate method
    if [[ ! "$METHOD" =~ ^(volume|rebuild|docker-cp)$ ]]; then
        print_error "Invalid method: $METHOD"
        echo "Usage: $0 [volume|rebuild|docker-cp]"
        echo ""
        echo "Methods:"
        echo "  volume     - Use volume mount (fastest, requires volume setup)"
        echo "  rebuild    - Rebuild Docker images (recommended for production)"
        echo "  docker-cp  - Copy files directly (temporary, for testing)"
        exit 1
    fi
    
    print_info "Deployment method: $METHOD"
    echo ""
    
    # Pre-deployment checks
    check_compose_file
    check_containers
    
    # Create backup
    create_backup
    
    # Deploy based on method
    case "$METHOD" in
        volume)
            deploy_volume
            ;;
        rebuild)
            deploy_rebuild
            ;;
        docker-cp)
            deploy_docker_cp
            ;;
    esac
    
    # Verify deployment
    verify_deployment
    
    echo ""
    print_info "Deployment finished successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Check logs: docker-compose -f $COMPOSE_FILE logs -f $WORKER_CONTAINER"
    echo "  2. Test a query from Admin Panel"
    echo "  3. Verify SSL settings in Elasticsearch config"
    echo ""
    
    # Ask if user wants to see logs
    read -p "Do you want to see the logs now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# Run main function
main "$@"
