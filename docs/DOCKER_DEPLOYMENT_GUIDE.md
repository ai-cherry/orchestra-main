fur# AI Orchestra Docker Deployment Guide

This guide explains the optimized Docker setup, deployment process, and CI/CD pipeline for the AI Orchestra project.

## Table of Contents

- [Optimized Dockerfile](#optimized-dockerfile)
- [Local Testing](#local-testing)
- [Manual Deployment](#manual-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

## Optimized Dockerfile

The AI Orchestra project uses a multi-stage Docker build to create efficient, secure container images for deployment to Cloud Run.

### Key Features

- **Multi-stage build**: Separates build dependencies from runtime dependencies
- **Layer caching**: Optimizes rebuild times by caching dependencies
- **Security enhancements**: Runs as non-root user
- **Health checks**: Includes container health monitoring
- **Environment configuration**: Sets appropriate Python environment variables

### Dockerfile Structure

1. **Builder Stage**:
   - Uses Python 3.11 slim image
   - Installs build dependencies
   - Configures Poetry
   - Exports dependencies to requirements.txt

2. **Runtime Stage**:
   - Uses Python 3.11 slim image
   - Installs runtime dependencies
   - Copies application code
   - Sets up non-root user
   - Configures health checks
   - Sets entry point and default command

### Benefits

- **Smaller image size**: Only includes necessary runtime dependencies
- **Improved security**: Runs as non-root user
- **Better caching**: Faster builds when only application code changes
- **Health monitoring**: Enables orchestration systems to monitor container health
- **Flexibility**: ENTRYPOINT/CMD pattern allows for runtime customization

## Local Testing

The `test_docker_build.sh` script provides a simple way to test the Docker build and application functionality locally.

### Usage

```bash
# Make the script executable
chmod +x test_docker_build.sh

# Run the test
./test_docker_build.sh
```

### What It Does

1. Builds the Docker image locally
2. Runs a container with the image
3. Tests the application's health endpoint
4. Cleans up the container

### Expected Output

```
=== AI Orchestra Docker Build Test ===
Cleaning up any existing test containers...
Building Docker image...
[...]
Running container for testing...
Waiting for container to start...
Checking container status...
✅ Container is running
Testing health endpoint...
✅ Health check passed
Cleaning up...
=== Test Completed Successfully ===
The Docker image is working correctly.
You can now proceed with deployment to Cloud Run.
```

## Manual Deployment

The `deploy.sh` script provides a comprehensive, consistent approach for deploying to GCP Cloud Run.

### Prerequisites

- GCP CLI (`gcloud`) installed and configured
- Docker installed and configured
- Appropriate GCP permissions:
  - Artifact Registry Writer
  - Cloud Run Admin
  - Secret Manager Accessor (if using secrets)

### Usage

```bash
# Make the script executable
chmod +x deploy.sh

# Basic deployment with defaults
./deploy.sh

# Deployment with custom settings
./deploy.sh \
  --project my-project \
  --region us-central1 \
  --service my-service \
  --env production \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 2
```

### Available Parameters

The script supports many customization options:

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

### Environment Configuration

You can create environment-specific configuration files:

- `.env.staging` - Environment variables for staging
- `.env.production` - Environment variables for production
- `secrets.staging.txt` - Secret references for staging
- `secrets.production.txt` - Secret references for production

Example `.env.staging`:
```
DEBUG=true
LOG_LEVEL=info
```

Example `secrets.staging.txt`:
```
DB_PASSWORD=projects/cherry-ai-project/secrets/db-password/versions/latest
API_KEY=projects/cherry-ai-project/secrets/api-key/versions/latest
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow for continuous integration and deployment.

### Workflow Features

- **Automated testing**: Runs tests on pull requests
- **Staging deployment**: Automatically deploys to staging on merges to main
- **Production deployment**: Manual trigger for production deployment
- **Workload Identity Federation**: Secure authentication to GCP
- **Deployment verification**: Validates deployments with health checks

### Workflow Location

The workflow configuration is in `.github/workflows/deploy-cloud-run.yml`

### Workflow Triggers

- **Pull requests**: Builds and tests the application
- **Pushes to main**: Deploys to staging environment
- **Manual trigger**: Deploys to staging or production environment

### Security

The workflow uses Workload Identity Federation for secure authentication to GCP, avoiding the need for long-lived service account keys.

## Troubleshooting

### Common Issues

#### Docker Build Failures

- **Issue**: Poetry dependency resolution fails
  - **Solution**: Check `pyproject.toml` for conflicting dependencies

- **Issue**: Build fails with permission errors
  - **Solution**: Ensure Docker has appropriate permissions

#### Deployment Failures

- **Issue**: Authentication errors with GCP
  - **Solution**: Verify service account permissions and Workload Identity Federation setup

- **Issue**: Cloud Run deployment fails
  - **Solution**: Check Cloud Run logs for application startup errors

#### Container Health Check Failures

- **Issue**: Health check endpoint returns non-200 status
  - **Solution**: Verify the application is properly handling the health endpoint

### Viewing Logs

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api" \
  --project=cherry-ai-project \
  --limit=50

# View container logs locally
docker logs <container-id>
```

### Getting Help

For additional assistance, contact the DevOps team or file an issue in the GitHub repository.

### Additional Documentation

For more detailed information about the deployment process, refer to:
- `CLOUD_RUN_DEPLOYMENT_GUIDE.md` - Comprehensive guide for the deployment script
- `SIMPLE_DEPLOYMENT.md` - Simplified deployment options
