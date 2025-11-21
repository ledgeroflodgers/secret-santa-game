#!/bin/bash

# Complete Secret Santa Deployment Script
# This script deploys both backend and frontend

set -e

# Configuration
ENVIRONMENT=${1:-dev}
DATA_BUCKET_NAME=${2:-secret-santa-game-data}

echo "=========================================="
echo "Secret Santa Complete Deployment"
echo "=========================================="
echo "Environment: ${ENVIRONMENT}"
echo "Data Bucket: ${DATA_BUCKET_NAME}"
echo "=========================================="

# Deploy backend first
echo ""
echo "Deploying backend..."
./deploy-backend.sh "${ENVIRONMENT}" "${DATA_BUCKET_NAME}"

# Wait a moment for CloudFormation to stabilize
echo ""
echo "Waiting for backend deployment to stabilize..."
sleep 5

# Deploy frontend
echo ""
echo "Deploying frontend..."
./deploy-frontend.sh "${ENVIRONMENT}"

echo ""
echo "=========================================="
echo "Complete Deployment Finished!"
echo "=========================================="
echo "Your Secret Santa application is now live!"
echo "=========================================="
