# Step-by-Step Guide: Deploying FastAPI Backend to Cloud Run

This guide walks you through the process of deploying your FastAPI backend to Google Cloud Run using Terraform.

## Prerequisites

Before you begin, ensure you have:

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
- [Docker](https://docs.docker.com/get-docker/) installed
- Access to the `cherry-ai-project` GCP project
- Proper authentication set up with GCP

## Step 1: Authenticate with Google Cloud

First, make sure you're authenticated with Google Cloud:

```bash
# Authenticate with your Google account
gcloud auth login

# Configure Docker to use gcloud credentials for GCR
gcloud auth configure-docker us-west2-docker.pkg.dev

# Set the default project
gcloud config set project cherry-ai-project

# Set the default region
gcloud config set run/region us-west2
```

## Step 2: Build the Docker Image

Navigate to the root directory of your project and build the Docker image:

```bash
# Navigate to the project root
cd /workspaces/orchestra-main

# Build the Docker image with a tag for Artifact Registry
docker build -t us-west2-docker.pkg.dev/cherry-ai-project/orchestra/orchestrator:dev-latest .
```

This command builds a Docker image using the `Dockerfile` in your project root and tags it for Google Artifact Registry.

## Step 3: Push the Docker Image to Google Artifact Registry

Push the built image to Google Artifact Registry:

```bash
# Create the repository if it doesn't exist
gcloud artifacts repositories create orchestra \
    --repository-format=docker \
    --location=us-west2 \
    --description="Orchestra Docker images"

# Push the image
docker push us-west2-docker.pkg.dev/cherry-ai-project/orchestra/orchestrator:dev-latest
```

## Step 4: Deploy to Cloud Run using Terraform

Now, use Terraform to deploy your Cloud Run service:

```bash
# Navigate to the dev environment directory
cd /workspaces/orchestra-main/infra/dev

# Initialize Terraform (if not done already)
terraform init

# Select or create the dev workspace
terraform workspace select dev || terraform workspace new dev

# Apply the Terraform configuration
terraform apply -var="env=dev"
```

This will create or update the Cloud Run service as defined in your Terraform configuration.

## Step 5: Verify the Deployment

After the deployment is complete, verify that your service is running:

```bash
# Get the URL of your deployed service
gcloud run services describe orchestrator-api-dev --region us-west2 --format="value(status.url)"

# Test the health endpoint
curl $(gcloud run services describe orchestrator-api-dev --region us-west2 --format="value(status.url)")/health
```

You should see a response from your health endpoint indicating the service is running.

## Step 6: Monitor Logs and Performance

Monitor your deployed service using Cloud Run logs:

```bash
# View logs for your service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-dev" --limit=10
```

## Common Issues and Troubleshooting

### Image Not Found

If Terraform can't find your image, ensure:
- The image was pushed successfully to Artifact Registry
- The image name in `infra/dev/main.tf` matches exactly what you pushed

### Service Unavailable

If the service deploys but returns errors:
- Check the Cloud Run logs for specific error messages
- Verify that all required environment variables are set in your Terraform configuration
- Ensure the service account has the necessary permissions

### Terraform State Issues

If you encounter Terraform state issues:
- Consider using remote state as described in `docs/infra.md`
- Run `terraform state list` to see what resources are currently tracked

## Updating Your Deployment

To update your deployment after making changes:

1. Rebuild your Docker image with the same tag
2. Push the new image to Artifact Registry
3. Cloud Run will automatically use the new image on the next request

For a complete redeployment, run the Terraform apply command again:

```bash
cd /workspaces/orchestra-main/infra/dev
terraform apply -var="env=dev"
```

## Next Steps

Once your API is deployed to Cloud Run, you can:

1. Connect your admin frontend to the deployed API
2. Set up CI/CD for automated deployments
3. Configure proper authentication and security for your API

Refer to `docs/infra.md` for more information on managing your infrastructure with Terraform.
