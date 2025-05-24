# MCP Server Deployment Guide

This guide explains how to deploy the MCP (Model Context Protocol) Server to Google Cloud Run using GitHub Actions.

## Prerequisites

1. A Google Cloud Platform (GCP) project with the following APIs enabled:

   - Cloud Run API (run.googleapis.com)
   - Container Registry API (containerregistry.googleapis.com)
   - Cloud Build API (cloudbuild.googleapis.com)
   - Security Token Service API (sts.googleapis.com)
   - IAM API (iam.googleapis.com)

2. GitHub repository with the MCP server code

3. Workload Identity Federation set up between GitHub and GCP

## Deployment Options

There are two ways to deploy the MCP server:

### Option 1: GitHub Actions Workflow (Recommended)

The repository includes a GitHub Actions workflow that automates the deployment process. This is the recommended approach as it uses Workload Identity Federation for secure authentication.

1. **Set up GitHub Secrets**

   The workflow requires the following secrets to be set in your GitHub repository:

   - `GCP_PROJECT_ID`: The ID of your GCP project (e.g., "cherry-ai-project")
   - `GCP_REGION`: The GCP region to deploy to (e.g., "us-central1")
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`: The Workload Identity Federation provider
   - `GCP_SERVICE_ACCOUNT`: The service account email for Workload Identity Federation

2. **Trigger the Workflow**

   You can trigger the workflow manually:

   1. Go to the "Actions" tab in your GitHub repository
   2. Select the "Deploy MCP Server" workflow
   3. Click "Run workflow"
   4. Select the environment to deploy to (dev, staging, or prod)
   5. Click "Run workflow"

   The workflow will:

   - Build a Docker image using the optimized Dockerfile
   - Push the image to Google Container Registry
   - Deploy the image to Cloud Run

### Option 2: Manual Deployment

If you prefer to deploy manually or need more control over the deployment process, you can use the following steps:

1. **Authenticate with GCP**

   ```bash
   # Authenticate with your service account key
   gcloud auth activate-service-account --key-file=credentials.json

   # Set the project and region
   gcloud config set project cherry-ai-project
   gcloud config set run/region us-central1
   ```

2. **Build and Push the Docker Image**

   ```bash
   # Build the Docker image
   docker build -t gcr.io/cherry-ai-project/mcp-server -f mcp_server/Dockerfile.optimized .

   # Configure Docker to use gcloud credentials
   gcloud auth configure-docker gcr.io

   # Push the image to Container Registry
   docker push gcr.io/cherry-ai-project/mcp-server
   ```

3. **Deploy to Cloud Run**

   ```bash
   # Deploy to Cloud Run
   gcloud run deploy mcp-server \
     --image gcr.io/cherry-ai-project/mcp-server \
     --platform managed \
     --allow-unauthenticated \
     --memory=1Gi \
     --cpu=1 \
     --concurrency=80 \
     --timeout=300s \
     --set-env-vars=ENV=dev,PROJECT_ID=cherry-ai-project
   ```

## Verifying the Deployment

After deployment, you can verify that the MCP server is running correctly:

1. **Check the Service URL**

   The deployment will output a service URL. You can access the following endpoints:

   - Health check: `https://your-service-url/health`
   - Status: `https://your-service-url/api/status`

2. **Check the Logs**

   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-server" --limit=10
   ```

## Troubleshooting

If you encounter issues during deployment, check the following:

1. **Authentication Issues**

   - Ensure the Security Token Service API (sts.googleapis.com) is enabled
   - Verify that the service account has the necessary permissions
   - Check that the Workload Identity Federation is set up correctly

2. **Build Issues**

   - Check the Dockerfile.optimized for any errors
   - Ensure all dependencies are correctly specified in pyproject.toml

3. **Runtime Issues**

   - Check the Cloud Run logs for any errors
   - Verify that the health check endpoint is responding correctly
   - Ensure the PORT environment variable is being used correctly

## Environment Variables

The MCP server supports the following environment variables:

- `PORT`: The port to listen on (default: 8080)
- `ENV`: The environment (dev, staging, prod)
- `PROJECT_ID`: The GCP project ID
- `MCP_USE_OPTIMIZED`: Whether to use optimized components (true/false)

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions for GCP](https://github.com/google-github-actions)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
