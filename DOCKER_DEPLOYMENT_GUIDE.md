# Orchestra Docker Deployment Guide

This guide provides detailed instructions for deploying the Orchestra application using Docker, covering both local testing and cloud deployment options.

## Prerequisites

Before beginning the deployment process, ensure the following prerequisites are met:

- Docker is properly installed and running (both client and server)
- GCP authentication is set up correctly
- Required environment variables are configured in `.env` file
- Necessary service accounts and permissions are configured

## Step 1: Verify Deployment Readiness

Run the deployment readiness verification script to ensure all prerequisites are met:

```bash
chmod +x ./verify_deployment_readiness.sh
./verify_deployment_readiness.sh
```

This script checks:
- Environment variables and configurations
- GCP authentication
- Service account credentials
- Docker availability
- API keys
- Redis configuration

## Step 2: Build the Docker Image Locally

Build the Docker image using the Dockerfile in the project root:

```bash
# Navigate to the project root
cd /workspaces/orchestra-main

# Build the Docker image with a descriptive tag
docker build -t orchestra:local .
```

## Step 3: Test the Docker Image Locally

Run the container locally to verify it works as expected:

```bash
# Run the container locally, mapping port 8000
docker run -p 8000:8000 --env-file .env orchestra:local

# In a separate terminal, test the API health endpoint
curl http://localhost:8000/api/health
```

## Step 4: Choose a Deployment Method

Based on your requirements, choose one of the following deployment methods:

### Option A: Quick Deployment to Cloud Run

This method uses the `deploy_to_cloud_run.sh` script to deploy directly to Cloud Run:

```bash
# Make the script executable
chmod +x ./deploy_to_cloud_run.sh

# Deploy to production environment
./deploy_to_cloud_run.sh prod
```

The script will:
1. Check prerequisites and authentication
2. Enable necessary GCP APIs
3. Build and tag the Docker image
4. Push to Google Artifact Registry
5. Deploy to Cloud Run with production-specific settings
6. Perform health checks on the deployed service

### Option B: Full Infrastructure Deployment with Terraform

For comprehensive infrastructure setup including supporting services:

```bash
# Navigate to the infrastructure directory
cd infra

# Initialize Terraform if not already done
terraform init

# Select or create the production workspace
terraform workspace select prod || terraform workspace new prod

# Apply the Terraform configuration
terraform apply -var="env=prod"
```

This approach:
- Sets up all required infrastructure (VPC, networks, Cloud Run, Redis, etc.)
- Provides better scalability and environment management
- Maintains infrastructure as code for reliability

### Option C: CI/CD Deployment via GitHub Actions

For automated deployment through CI/CD:

1. Ensure GitHub secrets are properly configured:
   ```bash
   chmod +x ./update_github_secrets.sh
   ./update_github_secrets.sh
   ```

2. Commit your changes and push to trigger the CI/CD pipeline:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

3. The GitHub Actions workflow will automatically:
   - Build and test the Docker image
   - Push to Google Artifact Registry
   - Deploy to Cloud Run
   - Perform validation checks

## Step 5: Verify Deployment

After deployment, verify the service is running correctly:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe orchestrator-api-prod \
  --region=us-central1 \
  --format='value(status.url)')

# Test the health endpoint
curl ${SERVICE_URL}/api/health
```

Additionally, check the logs to ensure there are no errors:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-prod" --limit=10
```

## Step 6: Setup Monitoring and Alerts

Set up monitoring and alerts for the production environment:

```bash
# Create monitoring dashboard
gcloud monitoring dashboards create --config-from-file=./config/monitoring_dashboard.json

# Create alerting policies for high error rates
gcloud alpha monitoring policies create \
  --display-name="Orchestra Prod Error Rate Alert" \
  --condition-filter="resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"orchestrator-api-prod\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code >= 500" \
  --condition-threshold-value=10 \
  --condition-threshold-filter="ABOVE" \
  --condition-aggregations-aligner=ALIGN_RATE \
  --condition-aggregations-period=300s \
  --condition-duration=300s \
  --alerting-channels=$(gcloud alpha monitoring channels list --format="value(name)" --limit=1)
```

## Troubleshooting

### Docker Build Issues

If Docker build fails:
- Check for syntax errors in the Dockerfile
- Ensure all required files are available
- Verify Docker daemon is running properly

### Deployment Failures

If deployment to Cloud Run fails:
- Check GCP authentication and permissions
- Verify the Docker image was built and pushed correctly
- Ensure all required environment variables are set
- Check service account permissions

### Runtime Issues

If the deployed service has runtime issues:
- Check the application logs via Cloud Logging
- Verify environment variables are correctly passed to the container
- Test Redis connectivity and authentication
- Check Portkey and OpenRouter API key validity

## Next Steps

After successful deployment:

1. Configure a custom domain if needed
2. Set up continuous integration/deployment if not already done
3. Implement a rollback strategy for failed deployments
4. Schedule regular backups of configuration and data
5. Set up cost monitoring and optimization

## Appendix: Environment Management

### Managing Multiple Environments

To deploy to different environments (dev, staging, prod):

```bash
# Development
./deploy_to_cloud_run.sh dev

# Staging
./deploy_to_cloud_run.sh stage

# Production
./deploy_to_cloud_run.sh prod
```

### Environment-Specific Configurations

Each environment has specific configurations:

- **Development**:
  - Min instances: 0
  - Max instances: 5
  - Memory: 2Gi
  - CPU: 1

- **Staging**:
  - Min instances: 1
  - Max instances: 10
  - Memory: 2Gi
  - CPU: 1

- **Production**:
  - Min instances: 1
  - Max instances: 20
  - Memory: 4Gi
  - CPU: 2
