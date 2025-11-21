#!/bin/bash

# Secret Santa Frontend Deployment Script
# This script builds and deploys the Angular frontend to AWS S3

set -e

# Configuration
ENVIRONMENT=${1:-dev}
API_URL=${2}
STACK_NAME="secret-santa-backend-${ENVIRONMENT}"

echo "=========================================="
echo "Secret Santa Frontend Deployment"
echo "=========================================="
echo "Environment: ${ENVIRONMENT}"
echo "=========================================="

# Check if API URL is provided or can be retrieved
if [ -z "${API_URL}" ]; then
    echo "API URL not provided, attempting to retrieve from CloudFormation..."
    
    if [ -f "api-url.txt" ]; then
        API_URL=$(cat api-url.txt)
        echo "Using API URL from api-url.txt: ${API_URL}"
    else
        API_URL=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_NAME}" \
            --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
            --output text 2>/dev/null || echo "")
        
        if [ -z "${API_URL}" ]; then
            echo "Error: Could not retrieve API URL."
            echo "Please provide it as the second argument: ./deploy-frontend.sh ${ENVIRONMENT} <API_URL>"
            exit 1
        fi
        echo "Retrieved API URL from CloudFormation: ${API_URL}"
    fi
fi

# Get S3 bucket name from CloudFormation
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

if [ -z "${BUCKET_NAME}" ]; then
    echo "Error: Could not retrieve S3 bucket name from CloudFormation stack."
    exit 1
fi

echo "S3 Bucket: ${BUCKET_NAME}"
echo "API URL: ${API_URL}"
echo ""

# Navigate to frontend directory
cd secret-santa-frontend

echo "Step 1: Installing dependencies..."
npm install

echo ""
echo "Step 2: Updating environment configuration..."
# Update the environment file with the actual API URL
sed "s|\${API_URL}|${API_URL}|g" src/environments/environment.prod.ts > src/environments/environment.prod.tmp.ts
mv src/environments/environment.prod.tmp.ts src/environments/environment.prod.ts

echo ""
echo "Step 3: Building Angular application for production..."
npm run build -- --configuration production

echo ""
echo "Step 4: Deploying to S3 with correct content types..."

# Upload HTML files
aws s3 cp dist/secret-santa-frontend/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*" \
  --include "*.html" \
  --content-type "text/html" \
  --cache-control "no-cache, no-store, must-revalidate"

# Upload CSS files
aws s3 cp dist/secret-santa-frontend/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*" \
  --include "*.css" \
  --content-type "text/css" \
  --cache-control "public, max-age=31536000"

# Upload JavaScript files
aws s3 cp dist/secret-santa-frontend/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*" \
  --include "*.js" \
  --content-type "application/javascript" \
  --cache-control "public, max-age=31536000"

# Upload other files (images, fonts, etc.)
aws s3 cp dist/secret-santa-frontend/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*.html" \
  --exclude "*.css" \
  --exclude "*.js" \
  --cache-control "public, max-age=31536000"

echo ""
echo "Step 5: Getting website URL..."
WEBSITE_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
    --output text)

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Website URL: ${WEBSITE_URL}"
echo "API URL: ${API_URL}"
echo "=========================================="

cd ..
