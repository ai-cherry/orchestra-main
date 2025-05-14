# AI Orchestra GCP Deployment Guide

This guide provides comprehensive instructions for deploying the AI Orchestra project to Google Cloud Platform (GCP) using GitHub Actions and GitHub Codespaces.

## Table of Contents

1. [Setup Overview](#setup-overview)
2. [GitHub Actions Workflow](#github-actions-workflow)
3. [Dev Container Configuration](#dev-container-configuration)
4. [Manual Deployment](#manual-deployment)
5. [Monitoring and Verification](#monitoring-and-verification)
6. [Customization Options](#customization-options)
7. [Troubleshooting](#troubleshooting)

## Setup Overview

The AI Orchestra project uses two main components for GCP deployment:

1. **GitHub Actions Workflow**: Automates the build, test, and deployment process to GCP Cloud Run
2. **Dev Container Configuration**: Sets up a consistent development environment with GCP authentication
3. **Deployment Script**: Provides a standardized approach for manual deployments

All components use Workload Identity Federation for secure authentication to GCP without storing service account keys in GitHub.

## GitHub Actions Workflow

The workflow file (`.github/workflows/deploy-cloud-run.yml`) handles the CI/CD pipeline:

- Triggers on pushes to the main branch
- Can be manually triggered with environment selection (staging/production)
- Uses Workload Identity Federation for secure GCP authentication
- Runs tests before deployment
- Builds and pushes a Docker container to Artifact Registry
- Deploys to Cloud Run with appropriate configuration
- Verifies the deployment with health checks

### Workflow Stages

1. **Build and Test**: Validates the application before deployment
2. **Deploy to Staging**: Automatically deploys to staging on pushes to main
3. **Deploy to Production**: Manual trigger with production environment selection

## Dev Container Configuration

The Dev Container configuration (`.devcontainer/devcontainer.json`) provides a consistent development environment:

- Installs Python 3.11, Poetry 1.7.1, and Google Cloud CLI
- Configures GCP authentication using Workload Identity Federation
- Sets environment variables for GCP tools
- Installs necessary VS Code extensions

## Manual Deployment

For manual deployments, use the consolidated `deploy_gcp_infra.sh` script:

```bash
# Make the script executable
chmod +x deploy_gcp_infra.sh

# Basic deployment with defaults
./deploy_gcp_infra.sh

# Deployment with custom settings
./deploy_gcp_infra.sh \
  --project my-project-id \
  --region us-central1 \
  --service my-service \
  --env production \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 2
```

### Script Features

- Comprehensive command-line parameters
- Environment-specific configuration from `.env.{environment}` files
- Secret management from `secrets.{environment}.txt` files
- Colorized output with clear progress indicators
- Automatic dependency checking
- Built-in deployment verification

## Monitoring and Verification

### Monitor the Deployment

For GitHub Actions deployments:

1. Go to the **Actions** tab in your GitHub repository
2. Select the running instance of the **Deploy to Cloud Run** workflow
3. Expand the logs for each step to monitor progress

For manual deployments, the script provides detailed output.

### Verify the Deployed Service

After deployment completes successfully:

#### Get the Service URL
The deployment outputs a URL (e.g., `https://orchestra-api-XXXXX-uc.a.run.app`).

#### Test the Service
Test with the provided health endpoint:

```bash
# For authenticated services
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://your-service-url/health

# For public services
curl https://your-service-url/health
```

#### Check Cloud Run Console
1. Log in to the Google Cloud Console
2. Navigate to Cloud Run and select your service
3. Confirm the service is running and check its status

#### CLI Verification
From your Codespace or local machine with gcloud installed, run:

```bash
gcloud run services describe YOUR_SERVICE_NAME --region YOUR_REGION
```

## Customization Options

### Environment-Specific Configuration

Create environment files for different deployment environments:

1. **Environment Variables**: Store in `.env.{environment}` files
   ```
   # .env.staging example
   DEBUG=true
   LOG_LEVEL=info
   DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
   ```

2. **Secrets Configuration**: Define in `secrets.{environment}.txt` files
   ```
   # secrets.staging.txt example
   API_KEY=projects/123456/secrets/api-key/versions/1
   DB_PASSWORD=projects/123456/secrets/db-password/versions/latest
   ```

### Command-Line Parameters

The `deploy_gcp_infra.sh` script supports many parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--project` | GCP project ID | cherry-ai-project |
| `--region` | GCP region | us-central1 |
| `--service` | Cloud Run service name | orchestra-api |
| `--env` | Deployment environment | staging |
| `--repo` | Artifact Registry repository name | orchestra-repo |
| `--min-instances` | Minimum instances | 0 |
| `--max-instances` | Maximum instances | 10 |
| `--memory` | Memory allocation | 512Mi |
| `--cpu` | CPU allocation | 1 |
| `--concurrency` | Request concurrency | 80 |
| `--timeout` | Request timeout | 300s |
| `--public` | Allow unauthenticated access | false |

## Troubleshooting

### Authentication Errors
- Ensure your Workload Identity Federation is correctly set up
- Verify the service account has the necessary permissions:
  - `roles/run.admin`
  - `roles/artifactregistry.admin`
  - `roles/iam.serviceAccountUser`

### Build Failures
- Check the Docker build logs for errors in your Dockerfile or dependencies
- Verify that Poetry is correctly configured in your project

### Deployment Failures
- Verify the Cloud Run region and service configuration match your GCP setup
- Check if the service account has the necessary permissions to deploy to Cloud Run
- Ensure Artifact Registry repository exists or can be created

### Dev Container Issues
- If the Dev Container fails to authenticate with GCP, check the Workload Identity Federation setup
- Run the verification script manually: `.devcontainer/setup_and_verify.sh`

### Logs
- Detailed logs are available in the GitHub Actions output
- Cloud Run logs can be viewed in the Cloud Run console under the "Logs" tab
- For manual deployments, check the logs output by the `deploy_gcp_infra.sh` script

## GitHub Codespaces Setup

### Rebuild Your Codespace

1. Open your Codespace in GitHub (or start a new one if it's not already running)
2. Open the Command Palette:
   - Windows/Linux: `Ctrl+Shift+P`
   - Mac: `Cmd+Shift+P`
3. Select **Codespaces: Rebuild Container**
4. Wait for the rebuild to complete. During this process, the `postCreateCommand` will run, authenticating your Codespace with GCP automatically.

### Verify Authentication

Once the Codespace rebuilds, open the terminal and run these commands to confirm everything is set up correctly:

```bash
# Check authenticated accounts
gcloud auth list

# Check the active project
gcloud config get-value project
```

If the service account is listed and active (marked with *), and the project ID matches your GCP project, the setup is complete.

## Additional Documentation

For more detailed information about the deployment process, refer to:
- `CLOUD_RUN_DEPLOYMENT_GUIDE.md` - Comprehensive guide for the deployment script
- `SIMPLE_DEPLOYMENT.md` - Simplified deployment options
- `docs/DOCKER_DEPLOYMENT_GUIDE.md` - Docker-specific deployment information
- `DEPLOYMENT_CHANGES.md` - Overview of recent deployment infrastructure changes
