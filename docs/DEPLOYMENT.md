# Secret Santa Game - AWS Deployment Guide

This guide explains how to deploy the Secret Santa Game application to AWS using S3 for the frontend and Lambda + API Gateway for the backend.

## Architecture Overview

- **Frontend**: Angular application hosted on AWS S3 with static website hosting
- **Backend**: Python Flask application running on AWS Lambda
- **API**: AWS API Gateway for RESTful endpoints
- **Database**: JSON data stored in S3 bucket with versioning enabled

## Prerequisites

Before deploying, ensure you have the following installed and configured:

1. **AWS CLI** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   ```bash
   aws --version
   ```

2. **AWS SAM CLI** - [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
   ```bash
   sam --version
   ```

3. **Node.js and npm** - For building the Angular frontend
   ```bash
   node --version
   npm --version
   ```

4. **Python 3.8+** - For the backend (Python 3.8, 3.9, 3.10, or 3.11)
   ```bash
   python3 --version
   ```
   
   **Note:** The Lambda runtime is configured for Python 3.8 by default. You can change this in `secret-santa-backend/template.yaml` if needed.

5. **AWS Credentials** - Configure your AWS credentials with a default region
   ```bash
   aws configure
   ```
   
   Make sure to set a default region (e.g., `us-east-1`) when prompted.

## Deployment Steps

### Option 1: Complete Deployment (Recommended)

Deploy both backend and frontend with a single command:

```bash
./deploy-all.sh [environment] [data-bucket-name]
```

**Example:**
```bash
./deploy-all.sh dev secret-santa-data
```

**Parameters:**
- `environment` (optional): Deployment environment (dev, staging, prod). Default: `dev`
- `data-bucket-name` (optional): Base name for the S3 data bucket. Default: `secret-santa-game-data`

### Option 2: Deploy Backend Only

Deploy just the backend Lambda function and API Gateway:

```bash
./deploy-backend.sh [environment] [data-bucket-name]
```

**Example:**
```bash
./deploy-backend.sh prod secret-santa-data
```

This will:
1. Install Python dependencies
2. Build the SAM application
3. Deploy to AWS CloudFormation
4. Create the API Gateway and Lambda function
5. Create the S3 data bucket
6. Output the API Gateway URL

### Option 3: Deploy Frontend Only

Deploy just the Angular frontend to S3:

```bash
./deploy-frontend.sh [environment] [api-url]
```

**Example:**
```bash
./deploy-frontend.sh dev https://abc123.execute-api.us-east-1.amazonaws.com/dev
```

**Note:** If you don't provide the API URL, the script will attempt to retrieve it from CloudFormation or the `api-url.txt` file.

This will:
1. Install npm dependencies
2. Build the Angular application for production
3. Update environment configuration with the API URL
4. Deploy to S3
5. Configure cache headers
6. Output the website URL

## Environment Configuration

### Backend Environment Variables

The backend automatically detects the deployment environment and uses S3 for data storage when running on Lambda.

Key environment variables:
- `ENVIRONMENT`: Deployment environment (dev, staging, prod)
- `DATA_BUCKET`: S3 bucket name for storing game data
- `USE_S3_DATABASE`: Set to 'true' for Lambda deployment

### Frontend Environment Configuration

The frontend uses environment-specific configuration files:

- **Development**: `src/environments/environment.ts`
  - API URL: `http://localhost:8080`
  
- **Production**: `src/environments/environment.prod.ts`
  - API URL: Replaced during deployment with actual API Gateway URL

## AWS Resources Created

The deployment creates the following AWS resources:

### Backend Stack (`secret-santa-backend-{environment}`)

1. **Lambda Function**: `secret-santa-api-{environment}`
   - Runtime: Python 3.8 (configurable in template.yaml)
   - Memory: 512 MB
   - Timeout: 30 seconds

2. **API Gateway**: `secret-santa-api-{environment}`
   - Stage: {environment}
   - CORS enabled for all origins

3. **S3 Data Bucket**: `{data-bucket-name}-{environment}-{AWS-Account-ID}`
   - Example: `secret-santa-game-data-dev-605868565364`
   - Versioning enabled
   - Server-side encryption (AES256)
   - Private access only

4. **S3 Frontend Bucket**: `secret-santa-frontend-{environment}-{AWS-Account-ID}`
   - Example: `secret-santa-frontend-dev-605868565364`
   - Static website hosting enabled
   - Public read access for website files

5. **IAM Roles**: Automatically created for Lambda execution with S3 access

## Post-Deployment

After successful deployment, you'll receive:

1. **API Gateway URL**: Use this to access the backend API
   ```
   https://abc123.execute-api.us-east-1.amazonaws.com/dev
   ```

2. **Frontend Website URL**: Use this to access the application
   ```
   http://secret-santa-frontend-dev.s3-website-us-east-1.amazonaws.com
   ```

### Testing the Deployment

1. **Health Check**: Test the backend API
   ```bash
   curl https://your-api-url/api/health
   ```

2. **Frontend**: Open the website URL in your browser

3. **Register a Participant**: Use the registration page to test the full flow

## Updating the Application

### Update Backend Only

```bash
./deploy-backend.sh [environment]
```

### Update Frontend Only

```bash
./deploy-frontend.sh [environment]
```

### Update Both

```bash
./deploy-all.sh [environment]
```

## Monitoring and Logs

### View Lambda Logs

```bash
aws logs tail /aws/lambda/secret-santa-api-{environment} --follow
```

### View CloudFormation Stack Status

```bash
aws cloudformation describe-stacks --stack-name secret-santa-backend-{environment}
```

### View S3 Bucket Contents

```bash
# Data bucket
aws s3 ls s3://{data-bucket-name}-{environment}/

# Frontend bucket
aws s3 ls s3://secret-santa-frontend-{environment}/
```

## Cleanup

To remove all AWS resources:

```bash
# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name secret-santa-backend-{environment} --region us-east-1

# Empty and delete the data bucket (if needed)
# Note: Replace {AWS-Account-ID} with your actual AWS account ID
aws s3 rm s3://{data-bucket-name}-{environment}-{AWS-Account-ID}/ --recursive
aws s3 rb s3://{data-bucket-name}-{environment}-{AWS-Account-ID}/

# Empty and delete the frontend bucket
aws s3 rm s3://secret-santa-frontend-{environment}-{AWS-Account-ID}/ --recursive
aws s3 rb s3://secret-santa-frontend-{environment}-{AWS-Account-ID}/
```

**Example for dev environment:**
```bash
aws cloudformation delete-stack --stack-name secret-santa-backend-dev --region us-east-1
aws s3 rm s3://secret-santa-game-data-dev-605868565364/ --recursive
aws s3 rb s3://secret-santa-game-data-dev-605868565364/
aws s3 rm s3://secret-santa-frontend-dev-605868565364/ --recursive
aws s3 rb s3://secret-santa-frontend-dev-605868565364/
```

## Troubleshooting

### Issue: "Stack already exists"

If you get this error, the stack already exists. Use `sam deploy` with the same parameters to update it, or delete the stack first.

### Issue: "Bucket name already taken"

S3 bucket names must be globally unique across all AWS accounts. The deployment scripts automatically append your AWS Account ID to bucket names to ensure uniqueness. If you still encounter this error, someone else may be using that exact combination. You can:
- Change the `data-bucket-name` parameter to something more unique
- The buckets will be named: `{bucket-name}-{environment}-{AWS-Account-ID}`

### Issue: "Access Denied" errors

Ensure your AWS credentials have the necessary permissions:
- CloudFormation full access
- Lambda full access
- API Gateway full access
- S3 full access
- IAM role creation

### Issue: CORS errors in browser

Check that:
1. The API Gateway has CORS enabled
2. The frontend is using the correct API URL
3. The Lambda function returns proper CORS headers

### Issue: Blank page or "Failed to load module script" error

This is caused by incorrect MIME types for JavaScript files. The deployment script now handles this automatically, but if you encounter this:

```bash
# Fix MIME types for JavaScript files
aws s3 cp s3://secret-santa-frontend-{environment}-{AWS-Account-ID}/ \
  s3://secret-santa-frontend-{environment}-{AWS-Account-ID}/ \
  --recursive --exclude "*" --include "*.js" \
  --content-type "application/javascript" \
  --metadata-directive REPLACE
```

Then hard refresh your browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows/Linux).

### Issue: Stack in ROLLBACK_COMPLETE state

If a previous deployment failed, delete the stack first:
```bash
aws cloudformation delete-stack --stack-name secret-santa-backend-{environment} --region us-east-1
```

Wait for deletion to complete, then redeploy.

### Issue: "Module not found" in Lambda

Ensure all dependencies are packaged correctly:
```bash
cd secret-santa-backend
pip3 install -r requirements.txt -t .
pip3 install boto3 -t .
```

**Note:** Use `pip3` on macOS/Linux, or `pip` on Windows.

## Cost Estimation

Approximate monthly costs for low-traffic usage (< 1000 requests/month):

- **Lambda**: Free tier covers 1M requests/month
- **API Gateway**: Free tier covers 1M requests/month
- **S3 Storage**: ~$0.023 per GB/month
- **S3 Requests**: Minimal cost for low traffic
- **Data Transfer**: Free tier covers 1 GB/month

**Estimated Total**: < $1/month for development/testing

## Security Considerations

1. **Data Bucket**: Private access only, accessed via Lambda
2. **Frontend Bucket**: Public read access for website hosting
3. **API Gateway**: CORS configured to allow all origins (adjust for production)
4. **Lambda Execution Role**: Minimal permissions (S3 read/write only)
5. **Encryption**: S3 server-side encryption enabled

## Production Recommendations

For production deployments, consider:

1. **Custom Domain**: Use Route 53 and CloudFront for custom domain
2. **HTTPS**: Enable CloudFront with SSL certificate
3. **CORS**: Restrict CORS to specific origins
4. **Monitoring**: Set up CloudWatch alarms for errors
5. **Backup**: Enable S3 versioning and cross-region replication
6. **Rate Limiting**: Implement API Gateway throttling
7. **Authentication**: Add Cognito or API keys for admin endpoints

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Verify all prerequisites are installed
4. Ensure AWS credentials are properly configured
