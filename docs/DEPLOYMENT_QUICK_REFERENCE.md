# AWS Deployment Quick Reference

## 🚀 Quick Deploy

```bash
# Deploy everything (recommended for first time)
./deploy-all.sh dev

# Deploy backend only
./deploy-backend.sh dev

# Deploy frontend only (requires API URL)
./deploy-frontend.sh dev <API_URL>

# Test deployment
./test-deployment.sh dev <API_URL>

# Deploy backend sample
cd secret-santa-backend
sam build
sam deploy --stack-name secret-santa-backend-dev --parameter-overrides Environment=dev DataBucketName=secret-santa-game-data --capabilities CAPABILITY_IAM --resolve-s3 --no-fail-on-empty-changeset
cd ..

# Deploy frontend sample
./deploy-frontend.sh dev https://7x0zqoelri.execute-api.us-east-1.amazonaws.com/dev
```

## 📋 Prerequisites

```bash
# Check installations
aws --version          # AWS CLI
sam --version          # AWS SAM CLI
node --version         # Node.js
python3 --version      # Python 3.11+

# Configure AWS
aws configure
```

## 🏗️ Architecture

**Local Dev:**
```
Angular (4200) → Flask (8080) → game_data.json
```

**AWS Prod:**
```
S3 Website → API Gateway → Lambda → S3 Data
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `deploy-all.sh` | Complete deployment |
| `deploy-backend.sh` | Backend only |
| `deploy-frontend.sh` | Frontend only |
| `test-deployment.sh` | Test deployment |
| `secret-santa-backend/template.yaml` | SAM infrastructure |
| `secret-santa-backend/lambda_handler.py` | Lambda handler |
| `secret-santa-backend/s3_database.py` | S3 database |
| `terraform/main.tf` | Terraform alternative |

## 🔍 Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/secret-santa-api-dev --follow

# View stack status
aws cloudformation describe-stacks --stack-name secret-santa-backend-dev

# List S3 contents
aws s3 ls s3://secret-santa-game-data-dev/
```

## 🧪 Testing

```bash
# Health check
curl <API_URL>/api/health

# Get participants
curl <API_URL>/api/participants

# Register participant
curl -X POST <API_URL>/api/participants \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User"}'
```

## 🗑️ Cleanup

```bash
# Delete stack
aws cloudformation delete-stack --stack-name secret-santa-backend-dev

# Empty buckets
aws s3 rm s3://secret-santa-game-data-dev/ --recursive
aws s3 rm s3://secret-santa-frontend-dev/ --recursive
```

## 💰 Cost

**Free Tier:**
- Lambda: 1M requests/month
- API Gateway: 1M requests/month
- S3: 5GB storage

**Estimated:** < $1/month for low traffic

## 🔒 Security

- ✅ Data bucket: Private
- ✅ Frontend bucket: Public read
- ✅ S3 encryption: Enabled
- ✅ Versioning: Enabled
- ✅ CORS: Configured

## 📚 Documentation

- `DEPLOYMENT.md` - Complete guide
- `QUICKSTART.md` - Quick start
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step
- `AWS_DEPLOYMENT_SUMMARY.md` - Implementation details

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Deployment fails | Check CloudFormation events |
| Lambda errors | Check CloudWatch logs |
| CORS errors | Verify API Gateway config |
| 404 errors | Verify API Gateway routes |
| Bucket name taken | Use unique bucket name |

## 🔄 CI/CD

**GitHub Actions:**
- Push to `main` → Deploy to prod
- Push to `develop` → Deploy to dev
- Manual workflow dispatch available

## 🎯 Common Commands

```bash
# Get API URL
aws cloudformation describe-stacks \
  --stack-name secret-santa-backend-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text

# Get Frontend URL
aws cloudformation describe-stacks \
  --stack-name secret-santa-backend-dev \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
  --output text

# Update deployment
./deploy-all.sh dev

# View recent logs
aws logs tail /aws/lambda/secret-santa-api-dev --since 1h
```

## 📞 Support

1. Check `DEPLOYMENT.md` troubleshooting section
2. Review CloudWatch logs
3. Verify AWS service health
4. Check AWS service quotas

---

**Need more details?** See `DEPLOYMENT.md` for comprehensive guide.
