# AWS Deployment Checklist

Use this checklist to ensure a successful deployment of the Secret Santa Game to AWS.

## Pre-Deployment Checklist

### Prerequisites
- [ ] AWS CLI installed and configured (`aws --version`)
- [ ] AWS SAM CLI installed (`sam --version`)
- [ ] Node.js and npm installed (`node --version`, `npm --version`)
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] AWS credentials configured with default region (`aws configure`)
- [ ] Verify AWS credentials work (`aws sts get-caller-identity`)
- [ ] Sufficient AWS permissions (Lambda, API Gateway, S3, CloudFormation, IAM)

### Configuration
- [ ] Choose unique S3 bucket base names (AWS Account ID will be appended automatically)
- [ ] Select AWS region (default: us-east-1) - must be configured in `aws configure`
- [ ] Decide on environment name (dev, staging, prod)
- [ ] Review and customize `config.example.sh` if needed
- [ ] Note: Actual bucket names will be `{bucket-name}-{environment}-{AWS-Account-ID}`

### Code Verification
- [ ] All backend tests pass (`cd secret-santa-backend && pytest`)
- [ ] All frontend tests pass (`cd secret-santa-frontend && npm test`)
- [ ] Backend runs locally (`python app.py`)
- [ ] Frontend runs locally (`npm start`)
- [ ] Local integration works (frontend can call backend)

## Deployment Steps

### Option 1: Complete Deployment (Recommended for First Time)

- [ ] Run complete deployment script:
  ```bash
  ./deploy-all.sh dev secret-santa-data
  ```

- [ ] Wait for deployment to complete (5-10 minutes)

- [ ] Note the API URL from output

- [ ] Note the Frontend URL from output

### Option 2: Backend Only

- [ ] Run backend deployment:
  ```bash
  ./deploy-backend.sh dev secret-santa-data
  ```

- [ ] Save the API URL from output

### Option 3: Frontend Only

- [ ] Ensure backend is deployed first

- [ ] Run frontend deployment:
  ```bash
  ./deploy-frontend.sh dev <API_URL>
  ```

## Post-Deployment Verification

### Automated Testing
- [ ] Run deployment tests:
  ```bash
  ./test-deployment.sh dev <API_URL>
  ```

- [ ] Verify all tests pass

### Manual Testing
- [ ] Open frontend URL in browser
- [ ] Verify home page loads
- [ ] Navigate to registration page
- [ ] Register a test participant
- [ ] Verify participant receives a number
- [ ] Navigate to participants page
- [ ] Verify participant appears in list
- [ ] Navigate to admin page
- [ ] Add a test gift
- [ ] Verify gift appears in list
- [ ] Test gift stealing functionality
- [ ] Verify steal counter increments
- [ ] Test gift locking after 3 steals

### API Testing
- [ ] Test health endpoint:
  ```bash
  curl <API_URL>/api/health
  ```

- [ ] Test participants endpoint:
  ```bash
  curl <API_URL>/api/participants
  ```

- [ ] Test gifts endpoint:
  ```bash
  curl <API_URL>/api/gifts
  ```

### AWS Console Verification
- [ ] Check CloudFormation stack status (CREATE_COMPLETE)
- [ ] Verify Lambda function exists
- [ ] Verify API Gateway is configured
- [ ] Verify S3 data bucket exists
- [ ] Verify S3 frontend bucket exists
- [ ] Check Lambda logs in CloudWatch
- [ ] Verify IAM roles are created

## Monitoring Setup

### CloudWatch
- [ ] Set up CloudWatch alarms for Lambda errors
- [ ] Set up CloudWatch alarms for API Gateway 5xx errors
- [ ] Configure log retention period
- [ ] Set up CloudWatch dashboard (optional)

### Cost Monitoring
- [ ] Enable AWS Cost Explorer
- [ ] Set up billing alerts
- [ ] Review estimated monthly costs
- [ ] Verify free tier usage

## Security Review

### Access Control
- [ ] Verify data bucket is private
- [ ] Verify frontend bucket allows public read
- [ ] Review IAM role permissions
- [ ] Verify Lambda execution role has minimal permissions

### CORS Configuration
- [ ] Verify CORS is configured correctly
- [ ] Test cross-origin requests
- [ ] Consider restricting origins for production

### Encryption
- [ ] Verify S3 encryption is enabled
- [ ] Verify data at rest is encrypted
- [ ] Verify HTTPS is used for all communications

## Documentation

- [ ] Document API URL for team
- [ ] Document Frontend URL for team
- [ ] Update project README with deployment info
- [ ] Share deployment guide with team
- [ ] Document any custom configurations

## Rollback Plan

### Preparation
- [ ] Document current CloudFormation stack version
- [ ] Note current Lambda function version
- [ ] Backup current S3 data (if applicable)
- [ ] Document rollback procedure

### Rollback Steps (if needed)
- [ ] Revert CloudFormation stack:
  ```bash
  aws cloudformation update-stack --stack-name <stack-name> --use-previous-template
  ```

- [ ] Or delete and redeploy previous version:
  ```bash
  aws cloudformation delete-stack --stack-name <stack-name>
  ./deploy-all.sh dev
  ```

## Production Deployment Additional Steps

### Before Production
- [ ] Review all security settings
- [ ] Set up custom domain (optional)
- [ ] Configure CloudFront for CDN (optional)
- [ ] Set up SSL certificate with ACM
- [ ] Enable CloudWatch detailed monitoring
- [ ] Set up automated backups
- [ ] Configure cross-region replication (optional)
- [ ] Review and adjust Lambda memory/timeout
- [ ] Set up API Gateway throttling
- [ ] Configure WAF rules (optional)

### Production Deployment
- [ ] Use production environment:
  ```bash
  ./deploy-all.sh prod secret-santa-data-prod
  ```

- [ ] Verify production deployment
- [ ] Run full test suite
- [ ] Perform load testing
- [ ] Monitor for 24 hours

### Post-Production
- [ ] Update DNS records (if using custom domain)
- [ ] Notify stakeholders of new URLs
- [ ] Monitor CloudWatch metrics
- [ ] Review costs after first billing cycle
- [ ] Schedule regular backups
- [ ] Document production configuration

## Cleanup (When No Longer Needed)

### Remove Resources
- [ ] Delete CloudFormation stack:
  ```bash
  aws cloudformation delete-stack --stack-name secret-santa-backend-dev
  ```

- [ ] Empty and delete data bucket:
  ```bash
  aws s3 rm s3://secret-santa-game-data-dev/ --recursive
  aws s3 rb s3://secret-santa-game-data-dev/
  ```

- [ ] Empty and delete frontend bucket:
  ```bash
  aws s3 rm s3://secret-santa-frontend-dev/ --recursive
  aws s3 rb s3://secret-santa-frontend-dev/
  ```

- [ ] Verify all resources are deleted in AWS Console

## Troubleshooting

### Common Issues
- [ ] If deployment fails, check CloudFormation events
- [ ] If Lambda errors, check CloudWatch logs
- [ ] If CORS errors, verify API Gateway configuration
- [ ] If 404 errors, verify API Gateway routes
- [ ] If S3 errors, verify bucket permissions
- [ ] If build fails, verify dependencies are installed

### Getting Help
- [ ] Review DEPLOYMENT.md troubleshooting section
- [ ] Check CloudWatch logs for errors
- [ ] Review AWS CloudFormation events
- [ ] Verify AWS service quotas
- [ ] Check AWS service health dashboard

## Notes

### Deployment Information
- **Date**: _______________
- **Environment**: _______________
- **API URL**: _______________
- **Frontend URL**: _______________
- **Deployed By**: _______________
- **Stack Name**: _______________
- **Region**: _______________

### Issues Encountered
_Document any issues and resolutions here_

---

## Quick Reference Commands

```bash
# Deploy everything
./deploy-all.sh dev

# Deploy backend only
./deploy-backend.sh dev

# Deploy frontend only
./deploy-frontend.sh dev <API_URL>

# Test deployment
./test-deployment.sh dev <API_URL>

# View Lambda logs
aws logs tail /aws/lambda/secret-santa-api-dev --follow

# View CloudFormation stack
aws cloudformation describe-stacks --stack-name secret-santa-backend-dev

# Delete stack
aws cloudformation delete-stack --stack-name secret-santa-backend-dev
```
