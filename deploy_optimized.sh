#!/bin/bash
# deploy_optimized.sh - Performance-optimized deployment script for AI Orchestra
# Uses GCP_MASTER_SERVICE_JSON for authentication

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting optimized deployment for AI Orchestra...${NC}"

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="ai-orchestra"
ENV=${1:-"dev"}  # Default to dev if not specified
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev"

# Check if GCP_MASTER_SERVICE_JSON is available
if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
    echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable is not set.${NC}"
    echo "Please set the GCP_MASTER_SERVICE_JSON environment variable with your GCP service account key."
    exit 1
fi

# Set up GCP credentials
echo -e "${YELLOW}Setting up GCP credentials...${NC}"
echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/gcp-credentials.json
chmod 600 /tmp/gcp-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-credentials.json"

# Authenticate with gcloud
echo -e "${YELLOW}Authenticating with Google Cloud...${NC}"
gcloud auth activate-service-account --key-file=/tmp/gcp-credentials.json
gcloud config set project ${PROJECT_ID}

# Configure Docker for Artifact Registry
echo -e "${YELLOW}Configuring Docker for Artifact Registry...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG} \
             -t ${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${ENV}-latest \
             -f Dockerfile.optimized .

# Push the Docker image
echo -e "${YELLOW}Pushing Docker image to Artifact Registry...${NC}"
docker push ${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}
docker push ${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${ENV}-latest

# Ensure Secret Manager secret exists
echo -e "${YELLOW}Ensuring Secret Manager secret exists...${NC}"
if ! gcloud secrets describe secret-management-key &>/dev/null; then
    echo -e "${YELLOW}Creating secret-management-key...${NC}"
    echo "${GCP_MASTER_SERVICE_JSON}" | gcloud secrets create secret-management-key \
        --data-file=- \
        --replication-policy="automatic"
else
    echo -e "${YELLOW}Updating secret-management-key...${NC}"
    echo "${GCP_MASTER_SERVICE_JSON}" | gcloud secrets versions add secret-management-key \
        --data-file=-
fi

# Deploy to Cloud Run with optimized settings
echo -e "${YELLOW}Deploying to Cloud Run with optimized settings...${NC}"
gcloud run deploy ${SERVICE_NAME}-${ENV} \
    --image ${ARTIFACT_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --cpu 2 \
    --memory 1Gi \
    --min-instances 1 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 300s \
    --set-env-vars="ENVIRONMENT=${ENV},OPTIMIZE_PERFORMANCE=true,STANDARD_MODE=true,VSCODE_DISABLE_WORKSPACE_TRUST=true,DISABLE_WORKSPACE_TRUST=true" \
    --set-secrets="GCP_SECRET_MANAGEMENT_KEY=secret-management-key:latest" \
    --service-account="orchestra-api-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME}-${ENV} --region ${REGION} --format='value(status.url)')

# Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
echo "Waiting for service to be ready..."
sleep 15

# Check if service is responding
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health || echo "failed")
if [ "$STATUS_CODE" != "200" ]; then
    echo -e "${RED}Deployment verification failed with status code: ${STATUS_CODE}${NC}"
    echo "Please check the logs for more information:"
    echo "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}-${ENV}' --limit 10"
else
    echo -e "${GREEN}Deployment verified successfully!${NC}"
fi

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# Clean up credentials
rm -f /tmp/gcp-credentials.json

# Instructions for setting up GitHub Actions
echo -e "\n${YELLOW}To set up GitHub Actions for automated deployment:${NC}"
echo "1. Add the following secrets to your GitHub repository:"
echo "   - GCP_MASTER_SERVICE_JSON: The GCP service account key"
echo "2. Create a .github/workflows/deploy.yml file with the optimized workflow"
echo "3. Push to your repository to trigger the workflow"

echo -e "\n${YELLOW}To set up GitHub Codespaces for development:${NC}"
echo "1. Add the following secrets to your GitHub repository or Codespaces:"
echo "   - GCP_MASTER_SERVICE_JSON: The GCP service account key"
echo "   - GH_CLASSIC_PAT_TOKEN: GitHub classic PAT token"
echo "   - GH_FINE_GRAINED_PAT_TOKEN: GitHub fine-grained PAT token"
echo "2. Configure the .devcontainer/devcontainer.json file"
echo "3. Open the repository in Codespaces"