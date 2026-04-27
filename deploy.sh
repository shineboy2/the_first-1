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

# Elasticsearch deployment (on response server)
ELASTICSEARCH_HOST="192.168.214.139"
ELASTICSEARCH_USER="response"
ELASTICSEARCH_PASS="1"

deploy_elasticsearch() {
    local HOST=$ELASTICSEARCH_HOST
    local USER=$ELASTICSEARCH_USER
    local PASS=$ELASTICSEARCH_PASS
    local TARGET_DIR="~/elasticsearch"
    
    echo -e "\n================================================="
    echo "🔍 Deploying Elasticsearch & Kibana to $HOST..."
    echo "================================================="
    
    # 1. Create target directory
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} "mkdir -p ${TARGET_DIR}"
    
    # 2. Copy docker-compose.elasticsearch.yml
    echo "🔄 Copying Elasticsearch configuration..."
    sshpass -p "$PASS" scp -o "StrictHostKeyChecking=no" \
        ./docker-compose.elasticsearch.yml ${USER}@${HOST}:${TARGET_DIR}/docker-compose.yml
    
    # 3. Deploy Elasticsearch stack
    echo "🐳 Starting Elasticsearch and Kibana containers..."
    sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
        "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker compose up --build -d"
    
    # 4. Wait for Elasticsearch to be ready
    echo "⏳ Waiting for Elasticsearch to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Checking Elasticsearch health..."
        
        if sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} \
            "curl -s http://localhost:9200/_cluster/health" > /dev/null 2>&1; then
            echo "✅ Elasticsearch is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ Elasticsearch failed to start after $max_attempts attempts"
            return 1
        fi
        
        sleep 5
        ((attempt++))
    done
    
    # 5. Wait for Kibana to be ready
    echo "⏳ Waiting for Kibana to be ready..."
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Checking Kibana health..."
        
        if sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" ${USER}@${HOST} \
            "curl -s http://localhost:5601/api/status" > /dev/null 2>&1; then
            echo "✅ Kibana is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "⚠️ Kibana may not be fully ready, but continuing..."
            break
        fi
        
        sleep 5
        ((attempt++))
    done
    
    echo "✅ Elasticsearch deployment completed!"
}

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
        --exclude="*.log" \
        --exclude=".pytest_cache" \
        --exclude="*.pyc" \
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
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec request-api alembic upgrade head"
            sshpass -p "$PASS" ssh -o "StrictHostKeyChecking=no" -t ${USER}@${HOST} \
                "cd ${TARGET_DIR} && echo '$PASS' | sudo -S docker exec request-api python init_db.py"
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
    deploy_elasticsearch
    deploy_network "response-network" "$RESPONSE_HOST" "$RESPONSE_USER" "$RESPONSE_PASS"
elif [ "$TARGET_NET" == "request" ]; then
    deploy_network "request-network" "$REQUEST_HOST" "$REQUEST_USER" "$REQUEST_PASS"
elif [ "$TARGET_NET" == "elasticsearch" ]; then
    deploy_elasticsearch
elif [ "$TARGET_NET" == "all" ]; then
    deploy_elasticsearch
    deploy_network "response-network" "$RESPONSE_HOST" "$RESPONSE_USER" "$RESPONSE_PASS"
    deploy_network "request-network" "$REQUEST_HOST" "$REQUEST_USER" "$REQUEST_PASS"
else
    echo "Usage: ./deploy.sh [response | request | elasticsearch | all] [--init] [--reset-db]"
    echo "Example: ./deploy.sh all --init --reset-db"
    echo "         ./deploy.sh elasticsearch"
    echo "         ./deploy.sh response"
fi
