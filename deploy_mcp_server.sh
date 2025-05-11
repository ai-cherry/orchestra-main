#!/bin/bash
# deploy_mcp_server.sh - Script to deploy the MCP server to Cloud Run

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-central1"  # Change this if you want to deploy to a different region
SERVICE_NAME="mcp-server"
KEY_FILE="credentials.json"

echo -e "${BLUE}=== Deploying MCP Server to Cloud Run ===${NC}"
echo -e "Project ID: ${PROJECT_ID}"
echo -e "Region: ${REGION}"
echo -e "Service Name: ${SERVICE_NAME}"
echo

# Step 1: Authenticate with GCP
echo -e "${YELLOW}Step 1: Authenticating with GCP${NC}"
if gcloud auth activate-service-account --key-file="$KEY_FILE"; then
  echo -e "${GREEN}✓ Authentication successful${NC}"
else
  echo -e "${RED}✗ Authentication failed${NC}"
  echo -e "  Please check that the Security Token Service API is enabled:"
  echo -e "  gcloud services enable sts.googleapis.com --project=${PROJECT_ID}"
  exit 1
fi

# Step 2: Set the project and region
echo -e "\n${YELLOW}Step 2: Setting project and region${NC}"
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
echo -e "${GREEN}✓ Project and region set${NC}"

# Step 3: Build and push the Docker image
echo -e "\n${YELLOW}Step 3: Building and pushing Docker image${NC}"
echo -e "  This may take a few minutes..."

# Check if Dockerfile exists in the mcp_server directory
if [ -f "mcp_server/Dockerfile" ]; then
  DOCKERFILE_PATH="mcp_server/Dockerfile"
elif [ -f "mcp_server/Dockerfile.optimized" ]; then
  DOCKERFILE_PATH="mcp_server/Dockerfile.optimized"
else
  echo -e "${RED}✗ Dockerfile not found in mcp_server directory${NC}"
  exit 1
fi

# Build and push the image
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
if gcloud builds submit --tag "$IMAGE_NAME" --dockerfile="$DOCKERFILE_PATH" .; then
  echo -e "${GREEN}✓ Docker image built and pushed successfully${NC}"
else
  echo -e "${RED}✗ Failed to build and push Docker image${NC}"
  echo -e "  Make sure the Container Registry API is enabled:"
  echo -e "  gcloud services enable containerregistry.googleapis.com --project=${PROJECT_ID}"
  exit 1
fi

# Step 4: Deploy to Cloud Run
echo -e "\n${YELLOW}Step 4: Deploying to Cloud Run${NC}"
if gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --timeout 300s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID}"; then
  
  echo -e "${GREEN}✓ Deployment successful${NC}"
  
  # Get the service URL
  SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --format="value(status.url)")
  echo -e "${GREEN}✓ MCP Server deployed to: ${SERVICE_URL}${NC}"
else
  echo -e "${RED}✗ Deployment failed${NC}"
  echo -e "  Make sure the Cloud Run API is enabled:"
  echo -e "  gcloud services enable run.googleapis.com --project=${PROJECT_ID}"
  exit 1
fi

echo -e "\n${BLUE}=== Deployment Complete ===${NC}"
echo -e "You can access your MCP Server at: ${SERVICE_URL}"
echo -e "To check the logs, run:"
echo -e "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --limit=10"