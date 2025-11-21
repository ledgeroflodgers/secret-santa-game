# Terraform Deployment for Secret Santa Game

This directory contains Terraform configuration for deploying the Secret Santa Game to AWS.

## Prerequisites

1. Install [Terraform](https://www.terraform.io/downloads.html) (>= 1.0)
2. Configure AWS credentials:
   ```bash
   aws configure
   ```

## Quick Start

1. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

2. Review the deployment plan:
   ```bash
   terraform plan
   ```

3. Deploy:
   ```bash
   terraform apply
   ```

4. Get the outputs:
   ```bash
   terraform output
   ```

## Configuration

### Variables

You can customize the deployment by creating a `terraform.tfvars` file:

```hcl
aws_region       = "us-east-1"
environment      = "dev"
data_bucket_name = "my-secret-santa-data"
```

Or pass variables on the command line:

```bash
terraform apply -var="environment=prod" -var="aws_region=us-west-2"
```

### Available Variables

- `aws_region` - AWS region (default: us-east-1)
- `environment` - Environment name (default: dev)
- `data_bucket_name` - Base name for data bucket (default: secret-santa-game-data)

## Outputs

After deployment, Terraform will output:

- `api_url` - API Gateway endpoint URL
- `frontend_url` - S3 website URL
- `data_bucket_name` - Name of the data bucket
- `frontend_bucket_name` - Name of the frontend bucket

## Deploying Frontend

After Terraform creates the infrastructure, deploy the frontend:

```bash
cd ..
./deploy-frontend.sh dev $(terraform -chdir=terraform output -raw api_url)
```

## Updating

To update the deployment:

```bash
terraform apply
```

## Destroying

To remove all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data including game state!

## State Management

Terraform stores state locally by default. For production, consider using remote state:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "secret-santa/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Comparison with SAM

| Feature | SAM | Terraform |
|---------|-----|-----------|
| Learning Curve | Lower | Higher |
| AWS-Specific | Yes | No (multi-cloud) |
| Local Testing | sam local | Limited |
| State Management | CloudFormation | Terraform state |
| Deployment Speed | Fast | Fast |

Choose SAM if you're AWS-focused and want simpler deployment. Choose Terraform if you need multi-cloud support or prefer infrastructure as code.
