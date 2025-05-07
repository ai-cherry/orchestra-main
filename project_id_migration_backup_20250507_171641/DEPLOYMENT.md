# Orchestra Deployment Guide

This guide explains how to deploy the Orchestra application to Google Cloud Platform (GCP) using the streamlined deployment process.

## Prerequisites

Before deploying, ensure you have the following:

1. Google Cloud SDK installed and configured
2. Docker installed for building container images
3. Terraform installed (if using the Terraform deployment method)
4. Access to the Google Cloud project: `agi-baby-cherry`
5. Proper authentication set up for GCP
6. All required API keys and credentials in your `.env` file

## Deployment Options

Orchestra supports two deployment methods:

1. **Terraform Deployment** (Recommended)
   - Uses infrastructure-as-code to provision and manage all resources
   - Creates all necessary resources including Cloud Run services, databases, VPC connectors, etc.
   - Easier to maintain and update infrastructure over time

2. **Direct Cloud Run Deployment**
   - Deploys the application container directly to Cloud Run
   - Requires pre-existing supporting infrastructure like databases, Redis, etc.
   - Useful for quick updates to the application code without changing infrastructure

## Environment Options

Three deployment environments are supported:

1. **dev** - Development environment for testing new features
2. **stage** - Staging environment for pre-production testing
3. **prod** - Production environment for end users

## Unified Deployment Script

The `deploy.sh` script provides a unified interface for all deployment scenarios. It handles:

- Environment setup and validation
- Authentication and API enablement
- Pre-deployment verification (for production)
- Deployment via Terraform or direct Cloud Run
- Post-deployment verification

### Usage

```bash
./deploy.sh [env] [method]
```

Where:
- `env` is one of: `dev`, `stage`, `prod` (defaults to `dev` if not specified)
- `method` is one of: `terraform`, `cloud-run` (defaults to `terraform` if not specified)

### Examples

Deploy to development environment using Terraform:
```bash
./deploy.sh dev terraform
# Or simply:
./deploy.sh dev
```

Deploy to production environment using Terraform:
```bash
./deploy.sh prod
```

Deploy directly to Cloud Run in the staging environment:
```bash
./deploy.sh stage cloud-run
```

## Deployment Configuration

### Terraform Variables

Terraform variables are defined in the following locations:

- **Development/Staging**: `infra/orchestra-terraform/terraform.tfvars`
- **Production**: `infra/prod.tfvars`

The unified deployment script automatically selects the appropriate variable file based on the target environment.

### Environment Variables

Environment variables for the deployed application are set from:

1. Terraform-managed Secret Manager secrets (for sensitive data)
2. Direct environment variable injection in the deployment configuration
3. Values from your `.env` file for local development

## Deployment Process

The unified deployment process follows these steps:

1. **Prerequisite Checks**: Verifies all required tools are installed
2. **Authentication**: Ensures proper GCP authentication
3. **API Enablement**: Enables required GCP APIs
4. **Pre-deployment Verification**: For production deployments, runs automated verification
5. **Deployment**:
   - For Terraform: Initializes, plans, and applies Terraform configuration
   - For Cloud Run: Builds and pushes Docker image, then deploys to Cloud Run
6. **Verification**: Checks that the deployed service is responding correctly

## Troubleshooting

If you encounter issues during deployment:

1. **Authentication Issues**:
   - Run `gcloud auth login` to authenticate
   - Check project access with `gcloud projects describe agi-baby-cherry`

2. **API Issues**:
   - Manually enable APIs in the GCP Console
   - Check API quotas for limits

3. **Terraform Issues**:
   - Run `terraform init -reconfigure` in the infrastructure directory
   - Check state with `terraform state list`

4. **Cloud Run Issues**:
   - Check service status in GCP Console
   - Review logs with `gcloud logging read "resource.type=cloud_run_revision"`

## Best Practices

1. Always test in development before deploying to production
2. Use the pre-deployment verification script for production deployments
3. Review Terraform plans carefully before applying
4. Maintain consistent environment variables across environments
5. Use version tags for container images instead of "latest"
