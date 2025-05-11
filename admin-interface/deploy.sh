#!/bin/bash
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-central1"}
ENV=${ENV:-"dev"}
SERVICE_NAME="ai-orchestra-admin-${ENV}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   AI Orchestra Admin Interface Deploy   ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "${YELLOW}Project:${NC} $PROJECT_ID"
echo -e "${YELLOW}Region:${NC} $REGION"
echo -e "${YELLOW}Environment:${NC} $ENV"
echo -e "${YELLOW}Service:${NC} $SERVICE_NAME"
echo -e "${GREEN}=========================================${NC}"

# Check if required tools are installed
command -v npm >/dev/null 2>&1 || { echo -e "${RED}Error: npm is required but not installed.${NC}" >&2; exit 1; }
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}Error: gcloud is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required but not installed.${NC}" >&2; exit 1; }

# Check if user is logged in to gcloud
gcloud auth print-access-token &>/dev/null || { 
  echo -e "${RED}Error: Not logged in to gcloud. Please run 'gcloud auth login' first.${NC}" >&2
  exit 1
}

# Check if project is set
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
  echo -e "${YELLOW}Setting project to $PROJECT_ID...${NC}"
  gcloud config set project $PROJECT_ID
fi

# Build the application
echo -e "${GREEN}Building the application...${NC}"
npm ci
npm run build

# Build and push Docker image
echo -e "${GREEN}Building and pushing Docker image...${NC}"
TAG=$(date +%Y%m%d-%H%M%S)
docker build -t ${IMAGE_NAME}:${TAG} -t ${IMAGE_NAME}:latest .
docker push ${IMAGE_NAME}:${TAG}
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image ${IMAGE_NAME}:${TAG} \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "API_URL=${API_URL}" \
  --project $PROJECT_ID

# Get the URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Service URL:${NC} $SERVICE_URL"
echo -e "${GREEN}=========================================${NC}"