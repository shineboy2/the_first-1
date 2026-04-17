#!/bin/bash

# =========================================================================
# Standard Deployment Script for Request & Response Networks
# =========================================================================

RESPONSE_HOST="192.168.214.141"
RESPONSE_USER="response"
RESPONSE_PASS="1"

REQUEST_HOST="192.168.214.146"
REQUEST_USER="request"
REQUEST_PASS="1"

deploy_network() {
    local NETWORK=$1
    local HOST=$2
    local USER=$3
    local PASS=$4
    # Use the network name as the remote directory (matches where .env already lives)
    local TARGET_DIR="~/${NETWORK}"
    
    echo -e "\n================================================="
    echo "🚀 Deploying $NETWORK to $HOST..."
    echo "================================================="
    
    # 1. Create target directory on remote server if it doesn't exist
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} "mkdir -p ${TARGET_DIR}"

    # 2. Sync files securely via rsync
    # We EXCLUDE .env so we don't accidentally overwrite the production environment variables!
    echo "🔄 Syncing files via rsync..."
    sshpass -p "$PASS" rsync -avz --delete \
        --exclude="node_modules" \
        --exclude=".next" \
        --exclude="venv" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="shared_data" \
        --exclude="postgres_data" \
        --exclude="redis_data" \
        --exclude=".env" \
        ./${NETWORK}/ ${USER}@${HOST}:${TARGET_DIR}/

    # 3. Reload Docker Containers with sudo
    # We use 'ssh -t' to allocate a pseudo-tty which sudo sometimes requires, 
    # and 'sudo -S' to pass the password securely via echo pipe.
    if [ "$RESET_DB" == "true" ]; then
        echo "🗑️ Cleaning Docker volumes for database reset..."
        sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
            "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose -p ${NETWORK} down -v"
    fi
    echo "🐳 Rebuilding and restarting Docker containers..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
        "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose -p ${NETWORK} up --build -d"
        
    # 4. Optional Initialization (for fresh deployments)
    if [ "$INIT_DB" == "true" ]; then
        echo "⚙️ Running database initialization and setup for $NETWORK..."
        # Wait for DB to be healthy
        sleep 5
        
        if [ "$NETWORK" == "request-network" ]; then
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec request-api python manage.py migrate"
        elif [ "$NETWORK" == "response-network" ]; then
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec response-api python manage.py migrate"
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec response-api python create_admin.py"
            # Optional: Add setup_initial_config.py call here if FTP details are known, but
            # usually setting it via Admin Panel once is sufficient if admin can login.
        fi
        echo "✅ Setup scripts completed."
    fi

    echo "✅ Deployment of $NETWORK completed successfully!"
}

# Input validation
INIT_DB="false"
RESET_DB="false"
TARGET_NET="$1"

if [ "$2" == "--init" ]; then
    INIT_DB="true"
    echo "⚙️ Initialization flag detected - will run setup scripts."
fi

if [ "$2" == "--reset-db" ] || [ "$3" == "--reset-db" ]; then
    RESET_DB="true"
    echo "🔄 Database reset flag detected - will clean volumes before deployment."
fi

if [ "$TARGET_NET" == "response" ]; then
    deploy_network "response-network" "$RESPONSE_HOST" "$RESPONSE_USER" "$RESPONSE_PASS"
elif [ "$TARGET_NET" == "request" ]; then
    deploy_network "request-network" "$REQUEST_HOST" "$REQUEST_USER" "$REQUEST_PASS"
elif [ "$TARGET_NET" == "all" ]; then
    deploy_network "response-network" "$RESPONSE_HOST" "$RESPONSE_USER" "$RESPONSE_PASS"
    deploy_network "request-network" "$REQUEST_HOST" "$REQUEST_USER" "$REQUEST_PASS"
else
    echo "Usage: ./deploy.sh [response | request | all] [--init] [--reset-db]"
    echo "Example: ./deploy.sh all --init --reset-db"
fi
