# Orchestra Deployment Summary

This document summarizes the deployment requirements and options for the Orchestra application based on code analysis.

## Deployment Prerequisites

### Required Accounts and Access

- **Google Cloud Platform Account** with access to `cherry-ai-project` project
- **GitHub Account** with access to the repository (for CI/CD deployment)
- **Docker Hub Account** (if using Docker Hub for image storage)

### Required API Keys and Credentials

- **GCP Service Account Key** with appropriate permissions
  - Current service account: `vertex-agent@cherry-ai-project.iam.gserviceaccount.com`
  - Key must be stored at `/tmp/vertex-agent-key.json`
- **Portkey API Key**: Present in `.env` file
- **OpenRouter API Key**: Present in `.env` file

### Required Infrastructure

- **Cloud Run** for hosting the API service
- **Firestore** for persistent memory storage
- **Redis** for caching (currently configured for localhost in `.env`)
- **Secret Manager** for secure credentials storage
- **VPC Network** for secure connectivity
- **Vertex AI Vector Search** for semantic search capabilities

## Current Deployment Status

### Missing Components

1. **GCP Service Account Key** - The key file is missing from `/tmp/vertex-agent-key.json`
2. **Required Tools**:
   - Google Cloud SDK (gcloud) is not installed
   - Docker is not installed

### Configuration Issues

1. **Redis Configuration** - Currently configured for localhost in `.env`, needs to point to a managed Redis instance for production
2. **Security Best Practices** - API keys should be moved to Secret Manager instead of .env file

## Deployment Options

### 1. GitHub Actions CI/CD (Recommended for Production)

- Complete workflows for testing, building, and deployment are already configured
- Requires GitHub repository secrets to be properly configured
- Supports both application deployment and infrastructure provisioning
- Handles both staging and production environments

### 2. Cloud Run Direct Deployment

- Use `deploy_to_cloud_run.sh` script for quick deployment
- Requires Docker and Google Cloud SDK
- Builds and deploys directly to Cloud Run
- Supports different environments (dev, stage, prod)

### 3. Terraform Infrastructure Deployment

- Use `run_terraform.sh` or Terraform directly for infrastructure provisioning
- Creates all required GCP resources (Cloud Run, Firestore, Redis, etc.)
- Configures networking, security, and monitoring
- Supports multiple environments through Terraform workspaces

## Deployment Steps

### Preparation (Run these scripts in order)

1. `./verify_deployment_readiness.sh` - Checks if environment is ready for deployment
2. `./prepare_for_deployment.sh` - Installs tools and sets up authentication
3. `./update_github_secrets.sh` - Configures GitHub secrets for CI/CD (if using GitHub Actions)

### Option 1: GitHub Actions Deployment

1. Configure secrets using the script or GitHub UI
2. Push changes to the main branch to trigger deployment
3. Monitor deployment progress in GitHub Actions

### Option 2: Direct Cloud Run Deployment

1. Run `./deploy_to_cloud_run.sh prod` for production
2. Wait for the deployment to complete
3. Test the deployed service using the provided URL

### Option 3: Terraform Infrastructure Deployment

1. Navigate to `infra` directory
2. Run `./run_terraform.sh` or use Terraform directly
3. Select appropriate workspace for environment
4. Apply Terraform configuration

## Security Considerations

1. **Service Account Keys**

   - Should be stored securely and rotated regularly
   - Should have minimal required permissions

2. **API Keys**

   - Should be stored in Secret Manager for production
   - Should be accessed securely in the application

3. **Network Security**
   - Use VPC networks for isolation
   - Configure firewall rules appropriately
   - Use private connections where possible

## Monitoring and Maintenance

1. **Logging and Monitoring**

   - Check the Terraform output for dashboard links
   - Set up alerts for critical metrics

2. **Regular Updates**
   - Keep dependencies updated
   - Rotate credentials regularly
   - Update infrastructure for security patches

## Additional Resources

- `docs/github_org_secrets.md` - Details on required GitHub secrets
- `docs/cloud_run_deployment.md` - Step-by-step guide for Cloud Run deployment
- `docs/gcp_deployment_guide.md` - Overview of GCP deployment architecture
- `infra/README.md` - Details on Terraform infrastructure
