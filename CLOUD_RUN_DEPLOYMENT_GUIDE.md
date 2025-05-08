# AI Orchestra Cloud Run Deployment Guide

This guide explains how to use the consolidated deployment script (`deploy.sh`) to deploy the AI Orchestra application to Google Cloud Run.

## Overview

The deployment script provides a clean, consistent approach for deploying the AI Orchestra application to Google Cloud Run. It combines the best features of previous deployment approaches into a single, well-structured script.

## Features

- **Well-structured** with clear sections and modular functions
- **Comprehensive parameter support** for customizing deployments
- **Colorized output** with clear status indicators
- **Environment-aware configuration** that adapts to staging, production, etc.
- **Automatic dependency checking** to ensure prerequisites are met
- **Proper error handling** with descriptive error messages
- **Built-in verification** to confirm successful deployment

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and initialized
- Docker installed and configured
- Appropriate GCP permissions to deploy to Cloud Run and Artifact Registry
- Project code in the current directory (including a valid Dockerfile)

## Non-Interactive Authentication Setup

To avoid browser-based authentication prompts when deploying, you can set up a service account key:

```bash
# Run the service account setup script
./setup_service_account.sh
```

This script will:
1. Guide you through creating or using an existing service account key
2. Place the key in the correct location (`$HOME/.gcp/service-account.json`)
3. Set up environment variables and verify authentication

Once set up, all deployment operations will use this key automatically, eliminating the need for browser-based authentication prompts.

## Usage

### Basic Usage

To deploy with default settings:

```bash
./deploy.sh
```

This will deploy with these defaults:
- Project ID: cherry-ai-project
- Region: us-central1
- Service name: orchestra-api
- Environment: staging
- Authenticated access only

### Customizing Deployment

You can customize any aspect of the deployment using command-line parameters:

```bash
./deploy.sh --project my-project-id --region us-east1 --service my-service --env production
```

### Full Parameter List

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
| `--help` | Show help message | - |

## Environment-Specific Configuration

The script automatically detects and uses environment-specific configuration:

1. **Environment Variables**: Reads from `.env.{environment}` files (e.g., `.env.staging`, `.env.production`)
   Example `.env.staging` file:
   ```
   DEBUG=true
   LOG_LEVEL=info
   DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
   ```

2. **Secrets Management**: Loads secrets from `secrets.{environment}.txt` files
   Example `secrets.staging.txt` file:
   ```
   API_KEY=projects/123456/secrets/api-key/versions/1
   DB_PASSWORD=projects/123456/secrets/db-password/versions/latest
   ```

## Deployment Process

The script follows this process:

1. **Parse Parameters**: Process command-line arguments
2. **Check Dependencies**: Verify gcloud and docker are installed
3. **Setup Environment**: Configure gcloud and prepare environment
4. **Enable APIs**: Enable required GCP APIs
5. **Setup Artifact Registry**: Create or use existing repository
6. **Build Image**: Build the Docker image
7. **Push Image**: Push to Artifact Registry
8. **Prepare Config**: Load environment variables and secrets
9. **Deploy**: Deploy to Cloud Run
10. **Verify**: Test the deployment with health checks

## Examples

### Deploy to Staging with Custom Settings

```bash
./deploy.sh --env staging --min-instances 1 --max-instances 5 --memory 1Gi
```

### Deploy to Production

```bash
./deploy.sh --env production --min-instances 2 --max-instances 20 --memory 2Gi --cpu 2
```

### Deploy with Public Access

```bash
./deploy.sh --env staging --public
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Failures**
   - Run `gcloud auth login` to refresh credentials
   - Ensure you have the necessary permissions in the GCP project

2. **Docker Build Failures**
   - Ensure Dockerfile is valid and all referenced files exist
   - Check Docker is running with `docker info`

3. **API Enablement Issues**
   - Manually enable APIs in GCP Console if automatic enablement fails

4. **Deployment Verification Failures**
   - Check app logs for application errors with:
     ```
     gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api"
     ```

## Improvements Over Previous Deployment Scripts

This consolidated script improves upon previous deployment approaches by:

1. **Consolidating functionality** from multiple scripts into a single, consistent approach
2. **Enhancing readability** with better logging and output formatting
3. **Improving error handling** with specific checks at each step
4. **Providing standardized configuration** across environments
5. **Adding built-in verification** to ensure successful deployments
