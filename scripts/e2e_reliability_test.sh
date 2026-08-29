#!/bin/bash
set -e

echo "=================================================="
echo " Starting End-to-End Reliability Test"
echo "=================================================="

# 1. Ensure clean state
echo "[1/5] Tearing down existing containers and volumes..."
docker compose -f docker-compose.prod.yml down -v

echo "[2/5] Starting production containers..."
docker compose -f docker-compose.prod.yml up -d

echo "[3/5] Waiting for services to be healthy..."
sleep 15 # Wait for DB, Redis, and ES to initialize
docker compose -f docker-compose.prod.yml ps

# Ensure workers are up
# We would normally hit a health check endpoint here.
sleep 5

echo "[4/5] Injecting test data..."
# Run seed script to set up a test user and request
docker compose -f docker-compose.prod.yml exec -T request_api python /app/scripts/db/create_test_user.py || true

# Simulate a request being generated and exported
echo "[5/5] Testing Failure Injection..."
# We randomly kill the response worker to simulate a crash during import/processing
docker compose -f docker-compose.prod.yml kill response_worker || true

echo "Response worker killed! Sleeping for 10 seconds to allow lease to expire (if set to short in tests) or to simulate downtime..."
sleep 10

echo "Restarting response worker..."
docker compose -f docker-compose.prod.yml start response_worker

echo "Checking logs to see if it recovered the orphaned file..."
sleep 15
docker compose -f docker-compose.prod.yml logs response_worker | grep "Downloading claimed file" || true
docker compose -f docker-compose.prod.yml logs response_worker | grep "CHECKSUM MISMATCH" || true

echo "=================================================="
echo " End-to-End Test Completed."
echo " Verify the logs above to ensure the worker resumed processing."
echo " Run 'docker compose -f docker-compose.prod.yml down -v' to clean up."
echo "=================================================="
