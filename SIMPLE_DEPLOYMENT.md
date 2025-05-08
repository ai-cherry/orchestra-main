# AI Orchestra Deployment Guide

This guide explains how to deploy the AI Orchestra application to Google Cloud Run using the consolidated deployment approach.

## Prerequisites

- Google Cloud account with access to the project
- `gcloud` CLI installed and configured
- Docker installed and running

## Deployment Options

### Option 1: Using the Consolidated Deployment Script

The recommended way to deploy is using our consolidated script:

```bash
# Make the script executable (if not already)
chmod +x deploy.sh

# Run the deployment script with default settings
./deploy.sh

# Or with custom parameters
./deploy.sh --project my-project-id --region us-east1 --service my-service --env production
```

The script supports many options to customize your deployment. Run `./deploy.sh --help` to see all available parameters.

### Option 2: Manual Deployment Steps

If you prefer to run the commands manually, follow these steps:

```bash
# Build the Docker image
REGION="us-central1"
PROJECT_ID="your-project-id"
SERVICE_NAME="orchestra-api"
REPO_NAME="orchestra-repo"
ENVIRONMENT="staging"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${ENVIRONMENT}"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Create repository if needed
gcloud artifacts repositories create ${REPO_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --project=${PROJECT_ID}

# Build and push the Docker image
docker build -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --platform=managed \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars=ENVIRONMENT=${ENVIRONMENT}
```

### Option 3: One-Line Deployment (Source-Based)

For a quick deployment directly from source:

```bash
gcloud run deploy orchestra-api \
  --source . \
  --region us-central1 \
  --platform managed
```

This uses Cloud Build to automatically build and deploy your application in one step.

### Option 4: GitHub Actions CI/CD

For automated deployments, a GitHub Actions workflow is included in `.github/workflows/deploy-cloud-run.yml`.

This workflow:
- Builds and tests the application
- Uses Workload Identity Federation for secure authentication
- Deploys to staging or production environments
- Includes verification steps

To use it:
1. Set up Workload Identity Federation for GitHub Actions
2. Push to the main branch or manually trigger the workflow with environment selection

## Environment Configuration

The deployment script supports environment-specific configuration:

1. **Environment Variables**: Store in `.env.{environment}` files (e.g., `.env.staging`, `.env.production`)

2. **Secrets**: Define in `secrets.{environment}.txt` files with format:
   ```
   SECRET_NAME=projects/123456/secrets/secret-name/versions/latest
   ```

## Accessing Your Application

After deployment, your application will be available at the URL provided in the deployment output.

You can test the application with:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" YOUR_SERVICE_URL/health
```

## Additional Documentation

For more detailed information about the deployment process, refer to the `CLOUD_RUN_DEPLOYMENT_GUIDE.md` file.
