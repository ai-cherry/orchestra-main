#!/bin/bash
# deploy_with_key.sh - Deployment script using service account key authentication
# This script deploys the MCP server to Cloud Run using a service account key

set -e

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
REGION=${2:-"us-central1"}
SERVICE_NAME="mcp-server"
ENVIRONMENT=${3:-"dev"}  # Default to dev if not specified
IMAGE_TAG=${4:-"latest"}  # Default to latest if not specified
KEY_FILE=${5:-"service-account-key.json"}  # Default key file name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of ${SERVICE_NAME} to ${ENVIRONMENT} environment...${NC}"

# Check if key file exists
if [ ! -f "${KEY_FILE}" ]; then
    echo -e "${RED}Service account key file not found: ${KEY_FILE}${NC}"
    echo -e "${YELLOW}Please provide a valid service account key file.${NC}"
    echo -e "${YELLOW}Usage: ./deploy_with_key.sh [project_id] [region] [environment] [image_tag] [key_file]${NC}"
    exit 1
fi

# Authenticate with service account key
echo -e "${GREEN}Authenticating with service account key...${NC}"
gcloud auth activate-service-account --key-file="${KEY_FILE}"
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/${KEY_FILE}"

# Verify authentication
echo -e "${GREEN}Verifying authentication...${NC}"
gcloud auth list

# Set project and region
gcloud config set project ${PROJECT_ID}
gcloud config set run/region ${REGION}

# Load environment-specific configurations
echo -e "${GREEN}Loading environment-specific configurations...${NC}"
if [ -f "config/environments/${ENVIRONMENT}.env" ]; then
    source "config/environments/${ENVIRONMENT}.env"
    echo -e "${GREEN}Loaded configuration for ${ENVIRONMENT} environment.${NC}"
    echo -e "${GREEN}Memory: ${MEMORY}${NC}"
    echo -e "${GREEN}CPU: ${CPU}${NC}"
    echo -e "${GREEN}Min Instances: ${MIN_INSTANCES}${NC}"
    echo -e "${GREEN}Max Instances: ${MAX_INSTANCES}${NC}"
else
    echo -e "${YELLOW}No environment-specific config found for ${ENVIRONMENT}, using defaults.${NC}"
    MEMORY="1Gi"
    CPU="1"
    MIN_INSTANCES="0"
    MAX_INSTANCES="10"
fi

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
  --memory=${MEMORY} \
  --cpu=${CPU} \
  --min-instances=${MIN_INSTANCES} \
  --max-instances=${MAX_INSTANCES} \
  --concurrency=80 \
  --timeout=300s \
  --set-env-vars=ENV=${ENVIRONMENT},PROJECT_ID=${PROJECT_ID}

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME}-${ENVIRONMENT} --platform managed --region ${REGION} --format='value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# Verify deployment
echo -e "${GREEN}Verifying deployment...${NC}"
sleep 15  # Wait for the service to be fully available
if curl -s ${SERVICE_URL}/health; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${YELLOW}Health check failed, but deployment completed.${NC}"
fi

echo -e "${GREEN}Deployment process completed!${NC}"