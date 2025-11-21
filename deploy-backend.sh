#!/bin/bash

# Secret Santa Backend Deployment Script
# This script deploys the backend to AWS Lambda using SAM

set -e

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME="secret-santa-backend-${ENVIRONMENT}"
DATA_BUCKET_NAME=${2:-secret-santa-game-data}

echo "=========================================="
echo "Secret Santa Backend Deployment"
echo "=========================================="
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name: ${STACK_NAME}"
echo "Data Bucket: ${DATA_BUCKET_NAME}-${ENVIRONMENT}"
echo "=========================================="

# Check if AWS SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: AWS SAM CLI is not installed."
    echo "Please install it from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured."
    echo "Please run 'aws configure' to set up your credentials."
    exit 1
fi

# Navigate to backend directory
cd secret-santa-backend

# Determine which pip command to use
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "Error: Neither pip nor pip3 found. Please install Python pip."
    exit 1
fi

echo ""
echo "Step 1: Installing Python dependencies..."
$PIP_CMD install -r requirements.txt -t .

echo ""
echo "Step 2: Adding boto3 for S3 operations..."
$PIP_CMD install boto3 -t .

echo ""
echo "Step 3: Building SAM application..."
sam build --template-file template.yaml

echo ""
echo "Step 4: Deploying to AWS..."
sam deploy \
    --stack-name "${STACK_NAME}" \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        DataBucketName="${DATA_BUCKET_NAME}" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --no-fail-on-empty-changeset

echo ""
echo "Step 5: Getting API Gateway URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "API URL: ${API_URL}"
echo ""
echo "Save this API URL for frontend deployment:"
echo "export API_URL=${API_URL}"
echo "=========================================="

# Save API URL to file for frontend deployment
echo "${API_URL}" > ../api-url.txt

cd ..
