#!/bin/bash
# deploy_wif.sh - Deployment script using Workload Identity Federation
# This script sets up and uses WIF for authentication with Google Cloud

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="mcp-server"
ENVIRONMENT=${1:-"dev"}  # Default to dev if not specified
IMAGE_TAG=${2:-"latest"}  # Default to latest if not specified

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of ${SERVICE_NAME} to ${ENVIRONMENT} environment using Workload Identity Federation...${NC}"

# Setup Workload Identity Federation if not already set up
if [ ! -f "wif_setup_complete" ]; then
    echo -e "${YELLOW}Setting up Workload Identity Federation...${NC}"
    
    # Create Workload Identity Pool
    gcloud iam workload-identity-pools create github-pool \
      --project=${PROJECT_ID} \
      --location=global \
      --display-name="GitHub Actions Pool"
    
    # Create Workload Identity Provider
    gcloud iam workload-identity-pools providers create-oidc github-provider \
      --project=${PROJECT_ID} \
      --location=global \
      --workload-identity-pool=github-pool \
      --display-name="GitHub Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --issuer-uri="https://token.actions.githubusercontent.com"
    
    # Create service account for GitHub Actions
    gcloud iam service-accounts create github-actions-sa \
      --project=${PROJECT_ID} \
      --description="Service account for GitHub Actions" \
      --display-name="GitHub Actions Service Account"
    
    # Grant necessary permissions
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
      --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
      --role="roles/run.admin"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
      --member="serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
      --role="roles/storage.admin"
    
    # Get the project number
    PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
    
    # Allow GitHub Actions to impersonate the service account
    gcloud iam service-accounts add-iam-policy-binding \
      github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com \
      --project=${PROJECT_ID} \
      --role="roles/iam.workloadIdentityUser" \
      --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/ai-cherry/orchestra-main"
    
    # Get the Workload Identity Provider resource name
    WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
    
    echo -e "${GREEN}Workload Identity Federation setup complete!${NC}"
    echo -e "${GREEN}Add the following secrets to your GitHub repository:${NC}"
    echo -e "${YELLOW}GCP_PROJECT_ID: ${PROJECT_ID}${NC}"
    echo -e "${YELLOW}GCP_REGION: ${REGION}${NC}"
    echo -e "${YELLOW}GCP_WORKLOAD_IDENTITY_PROVIDER: ${WIF_PROVIDER}${NC}"
    echo -e "${YELLOW}GCP_SERVICE_ACCOUNT: github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
    
    # Mark WIF setup as complete
    touch wif_setup_complete
else
    echo -e "${GREEN}Workload Identity Federation already set up.${NC}"
fi

# Note: This script assumes it's being run in a GitHub Actions workflow
# where the WIF authentication has already been set up by the google-github-actions/auth action

# Verify authentication
echo -e "${GREEN}Verifying authentication...${NC}"
gcloud auth list

# Set project and region
gcloud config set project ${PROJECT_ID}
gcloud config set run/region ${REGION}

# Build and push Docker image
echo -e "${GREEN}Building and pushing Docker image...${NC}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}-${ENVIRONMENT}:${IMAGE_TAG}"

# Check if Dockerfile.optimized exists, otherwise use regular Dockerfile
if [ -f "mcp_server/Dockerfile.optimized" ]; then
    DOCKERFILE="mcp_server/Dockerfile.optimized"
else
    DOCKERFILE="mcp_server/Dockerfile"
fi

echo -e "${GREEN}Using Dockerfile: ${DOCKERFILE}${NC}"

# Build the Docker image
docker build -t ${IMAGE_NAME} -f ${DOCKERFILE} .

# Configure Docker to use gcloud credentials
gcloud auth configure-docker gcr.io

# Push the Docker image
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME}-${ENVIRONMENT} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=80 \
  --timeout=300s \
  --set-env-vars=ENV=${ENVIRONMENT},PROJECT_ID=${PROJECT_ID}

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME}-${ENVIRONMENT} --platform managed --region ${REGION} --format='value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# Verify deployment
echo -e "${GREEN}Verifying deployment...${NC}"
curl -s ${SERVICE_URL}/health || echo -e "${RED}Health check failed!${NC}"

echo -e "${GREEN}Deployment process completed!${NC}"