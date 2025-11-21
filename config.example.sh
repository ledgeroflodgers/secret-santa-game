#!/bin/bash

# Secret Santa Deployment Configuration
# Copy this file to config.sh and customize for your deployment

# AWS Region
export AWS_REGION="us-east-1"

# Environment (dev, staging, prod)
export ENVIRONMENT="dev"

# S3 Bucket Names (must be globally unique)
export DATA_BUCKET_NAME="secret-santa-game-data"
export FRONTEND_BUCKET_NAME="secret-santa-frontend"

# Stack Name
export STACK_NAME="secret-santa-backend-${ENVIRONMENT}"

# Optional: Custom domain settings (for production)
# export CUSTOM_DOMAIN="secretsanta.example.com"
# export CERTIFICATE_ARN="arn:aws:acm:us-east-1:123456789012:certificate/..."

# Optional: CloudWatch Log Retention (days)
export LOG_RETENTION_DAYS=7

# Optional: Lambda Configuration
export LAMBDA_MEMORY_SIZE=512
export LAMBDA_TIMEOUT=30
