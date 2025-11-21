# Secret Santa Game - Quick Start Guide

## Local Development

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd secret-santa-backend
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend:
   ```bash
   python app.py
   ```

   The backend will be available at `http://localhost:8080`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd secret-santa-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:4200`

## AWS Deployment

### Prerequisites

Install required tools:
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- Node.js and npm
- Python 3.8+ (3.8, 3.9, 3.10, or 3.11)

Configure AWS credentials with a default region:
```bash
aws configure
# When prompted, set region to: us-east-1 (or your preferred region)
```

### Deploy Everything

Run the complete deployment script:

```bash
./deploy-all.sh dev
```

This will:
1. Deploy the backend to AWS Lambda
2. Create API Gateway endpoints
3. Create S3 buckets for data and frontend
4. Build and deploy the Angular frontend
5. Output the website URL

### Deploy Backend Only

```bash
./deploy-backend.sh dev
```

### Deploy Frontend Only

```bash
./deploy-frontend.sh dev
```

## Testing the Deployment

1. **Health Check**:
   ```bash
   curl https://your-api-url/api/health
   ```

2. **Open the Website**:
   Visit the frontend URL provided after deployment

3. **Register a Participant**:
   - Go to the registration page
   - Enter a name
   - Verify you receive a unique number

## Common Commands

### View Lambda Logs
```bash
aws logs tail /aws/lambda/secret-santa-api-dev --follow
```

### View S3 Data
```bash
# Replace {AWS-Account-ID} with your actual AWS account ID
aws s3 ls s3://secret-santa-game-data-dev-{AWS-Account-ID}/
aws s3 cp s3://secret-santa-game-data-dev-{AWS-Account-ID}/game_data.json -

# Example:
aws s3 ls s3://secret-santa-game-data-dev-605868565364/
aws s3 cp s3://secret-santa-game-data-dev-605868565364/game_data.json -
```

### Update Deployment
```bash
./deploy-all.sh dev
```

### Delete Everything
```bash
aws cloudformation delete-stack --stack-name secret-santa-backend-dev --region us-east-1
```

## Architecture

- **Frontend**: Angular on S3 static website hosting
- **Backend**: Python Flask on AWS Lambda
- **API**: AWS API Gateway
- **Database**: JSON file in S3 with versioning

## Next Steps

- Read the full [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed information
- Customize the application for your needs
- Set up production environment with custom domain
- Add authentication for admin endpoints

## Support

For issues:
1. Check CloudWatch logs
2. Verify AWS credentials
3. Review the troubleshooting section in DEPLOYMENT.md
