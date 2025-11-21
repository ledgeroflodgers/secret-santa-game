# Known Issues and Solutions

This document lists known issues encountered during deployment and their solutions.

## 1. MIME Type Issues with S3 Static Website

### Issue
JavaScript files served from S3 static website hosting have incorrect MIME type (`binary/octet-stream` instead of `application/javascript`), causing browser error:
```
Failed to load module script: Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "binary/octet-stream"
```

### Root Cause
The `aws s3 sync` command doesn't automatically set correct content types for files.

### Solution
The deployment script now explicitly sets content types during upload:
```bash
# Upload JavaScript files with correct MIME type
aws s3 cp dist/secret-santa-frontend/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*" \
  --include "*.js" \
  --content-type "application/javascript"
```

### Manual Fix
If you encounter this after deployment:
```bash
aws s3 cp s3://secret-santa-frontend-dev-{AWS-Account-ID}/ \
  s3://secret-santa-frontend-dev-{AWS-Account-ID}/ \
  --recursive --exclude "*" --include "*.js" \
  --content-type "application/javascript" \
  --metadata-directive REPLACE
```

Then hard refresh your browser (Cmd+Shift+R or Ctrl+Shift+R).

---

## 2. S3 Bucket Permission Errors (403 Forbidden)

### Issue
Lambda function gets 403 Forbidden errors when trying to access S3 bucket:
```
ClientError: An error occurred (403) when calling the HeadObject operation: Forbidden
```

### Root Cause
The IAM policy for Lambda was referencing the bucket name parameter instead of the actual bucket resource.

### Solution
Updated `template.yaml` to reference the bucket resource directly:
```yaml
Policies:
  - S3CrudPolicy:
      BucketName: !Ref DataBucket  # References the actual bucket resource
```

---

## 3. Bucket Name Already Exists

### Issue
CloudFormation fails with:
```
Resource handler returned message: "secret-santa-frontend-dev already exists"
```

### Root Cause
S3 bucket names must be globally unique across all AWS accounts.

### Solution
Bucket names now automatically include AWS Account ID:
- Format: `{bucket-name}-{environment}-{AWS-Account-ID}`
- Example: `secret-santa-frontend-dev-605868565364`

Updated in `template.yaml`:
```yaml
BucketName: !Sub 'secret-santa-frontend-${Environment}-${AWS::AccountId}'
```

---

## 4. Stack in ROLLBACK_COMPLETE State

### Issue
Deployment fails with:
```
Stack is in ROLLBACK_COMPLETE state and can not be updated
```

### Root Cause
A previous deployment failed and CloudFormation rolled back, leaving the stack in an unusable state.

### Solution
Delete the stack before redeploying:
```bash
aws cloudformation delete-stack --stack-name secret-santa-backend-dev --region us-east-1
```

Wait for deletion to complete (check in AWS Console or use `aws cloudformation wait stack-delete-complete`), then redeploy.

---

## 5. pip Command Not Found

### Issue
Deployment script fails with:
```
pip: command not found
```

### Root Cause
On macOS and some Linux systems, Python 3 uses `pip3` instead of `pip`.

### Solution
The deployment script now automatically detects and uses the correct command:
```bash
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
fi
```

---

## 6. Python Version Mismatch

### Issue
SAM build fails with:
```
Binary validation failed for python, searched for python in following locations: ['/usr/bin/python3'] 
which did not satisfy constraints for runtime: python3.11
```

### Root Cause
The system Python version doesn't match the Lambda runtime specified in `template.yaml`.

### Solution
Updated `template.yaml` to use Python 3.8 (more widely available):
```yaml
Runtime: python3.8
```

You can change this to match your system Python version (3.8, 3.9, 3.10, or 3.11).

---

## 7. AWS Region Not Configured

### Issue
AWS CLI commands fail with:
```
You must specify a region. You can also configure your region by running "aws configure".
```

### Root Cause
AWS CLI doesn't have a default region configured.

### Solution
Configure a default region:
```bash
aws configure set default.region us-east-1
```

Or run `aws configure` and set the region when prompted.

---

## 8. Lambda Environment Variable Mismatch

### Issue
Lambda can't find S3 bucket because environment variable has wrong bucket name.

### Root Cause
The `DATA_BUCKET` environment variable was set to the parameter value instead of the actual bucket name (which includes Account ID).

### Solution
Updated `template.yaml` to reference the bucket resource:
```yaml
Environment:
  Variables:
    DATA_BUCKET: !Ref DataBucket  # References actual bucket name
```

---

## 9. Angular Build Budget Exceeded

### Issue
Angular production build fails with:
```
exceeded maximum budget. Budget 4.00 kB was not met by 2.49 kB with a total of 6.49 kB
```

### Root Cause
CSS files in admin and participants components exceed the default budget limits.

### Solution
Updated `angular.json` to increase budget limits:
```json
{
  "type": "anyComponentStyle",
  "maximumWarning": "6kb",
  "maximumError": "10kb"
}
```

---

## Best Practices to Avoid Issues

1. **Always configure AWS region**: Run `aws configure` and set a default region
2. **Use hard refresh**: After deploying frontend changes, use Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
3. **Check CloudFormation events**: If deployment fails, check CloudFormation console for detailed error messages
4. **Verify Python version**: Ensure your Python version matches the Lambda runtime in `template.yaml`
5. **Clean up failed stacks**: Delete stacks in ROLLBACK_COMPLETE state before redeploying
6. **Use deployment scripts**: The automated scripts handle most common issues automatically

---

## Getting Help

If you encounter an issue not listed here:

1. Check CloudWatch Logs:
   ```bash
   aws logs tail /aws/lambda/secret-santa-api-dev --follow
   ```

2. Check CloudFormation Events:
   ```bash
   aws cloudformation describe-stack-events --stack-name secret-santa-backend-dev --max-items 20
   ```

3. Verify resources exist:
   ```bash
   aws s3 ls | grep secret-santa
   aws lambda list-functions | grep secret-santa
   ```

4. Check IAM permissions:
   ```bash
   aws iam get-user
   ```
