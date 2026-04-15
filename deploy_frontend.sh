#!/bin/bash
set -e

# Define directories
LOCAL_BASE="/home/docker/the_first/the_first/response-network/admin-panel"
REMOTE_BASE="/opt/response-network/admin-panel"
SERVER="response@192.168.214.141"

echo "📦 Bundling updated frontend files..."
tar -cvf frontend_update.tar \
    -C "$LOCAL_BASE" \
    "app/dashboard/layout.tsx" \
    "app/(auth)/api.ts" \
    "lib/stores/auth-store.ts" \
    "lib/services/admin-api.ts"

echo "⬆️ Uploading bundle to server..."
scp frontend_update.tar "$SERVER:/tmp/"

echo "🚀 Deploying on server..."
ssh -t "$SERVER" "
    set -e
    echo '🔓 Extracting files (needs sudo)...'
    sudo tar -xvf /tmp/frontend_update.tar -C $REMOTE_BASE
    
    echo '🗑️ Removing stale cache directory if exists...'
    sudo rm -rf $REMOTE_BASE/app/dashboard/cache
    
    echo '🏗️  Rebuilding Admin Panel...'
    cd /opt/response-network
    sudo docker compose build admin-panel
    sudo docker compose up -d admin-panel
    
    echo '🧹 Cleaning up...'
    rm /tmp/frontend_update.tar
    
    echo '✅ Deployment Complete!'
"

rm frontend_update.tar
