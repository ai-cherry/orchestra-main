#!/bin/bash
# deploy_anywhere.sh - Simple deployment script for AI Orchestra with hardcoded GCP auth
set -e

# Default values
IMAGE_NAME="ai-orchestra"
CONTAINER_REGISTRY="gcr.io/cherry-ai-project"
TAG="latest"
DEPLOY_TARGET=""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage information
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --image-name NAME     Docker image name (default: ai-orchestra)"
  echo "  --registry URL        Container registry URL (default: gcr.io/cherry-ai-project)"
  echo "  --tag TAG             Image tag (default: latest)"
  echo "  --target PLATFORM     Deployment target (render, fly, aws, azure, digital-ocean)"
  echo "  --help                Show this help message"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --image-name)
      IMAGE_NAME="$2"
      shift 2
      ;;
    --registry)
      CONTAINER_REGISTRY="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --target)
      DEPLOY_TARGET="$2"
      shift 2
      ;;
    --help)
      show_usage
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      ;;
  esac
done

FULL_IMAGE_NAME="${CONTAINER_REGISTRY}/${IMAGE_NAME}:${TAG}"

echo -e "${BLUE}=== AI Orchestra Deployment ===${NC}"
echo -e "${BLUE}Image: ${FULL_IMAGE_NAME}${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we have a service account key for non-interactive auth
if [[ -f "$HOME/.gcp/service-account.json" ]]; then
  echo -e "${YELLOW}Authenticating with GCP service account key...${NC}"
  gcloud auth activate-service-account --quiet --key-file=$HOME/.gcp/service-account.json
  export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
  echo -e "${GREEN}Successfully authenticated with GCP${NC}"
elif [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
  echo -e "${YELLOW}Creating service account key file from environment variable...${NC}"
  mkdir -p $HOME/.gcp
  echo "$GCP_MASTER_SERVICE_JSON" > $HOME/.gcp/service-account.json
  gcloud auth activate-service-account --quiet --key-file=$HOME/.gcp/service-account.json
  export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
  echo -e "${GREEN}Successfully authenticated with GCP${NC}"
else
  echo -e "${YELLOW}No service account credentials found, continuing with default auth...${NC}"
  echo -e "${YELLOW}To avoid interactive prompts, set up a service account key at $HOME/.gcp/service-account.json${NC}"
fi

# Step 1: Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${FULL_IMAGE_NAME} .

# Step 2: Push to container registry
echo -e "${YELLOW}Pushing to container registry...${NC}"
docker push ${FULL_IMAGE_NAME}

# Step 3: Deploy based on target platform
if [ -n "$DEPLOY_TARGET" ]; then
  echo -e "${YELLOW}Deploying to ${DEPLOY_TARGET}...${NC}"
  
  case $DEPLOY_TARGET in
    render)
      echo "For Render.com deployment:"
      echo "1. Create a render.yaml file:"
      echo "   services:"
      echo "     - type: web"
      echo "       name: ai-orchestra"
      echo "       env: docker"
      echo "       dockerfilePath: ./Dockerfile"
      echo "       envVars:"
      echo "         - key: PORT"
      echo "           value: 8080"
      echo "2. Connect your GitHub repo to Render.com"
      echo "3. Deploy from the Render dashboard"
      ;;
    fly)
      echo "For Fly.io deployment:"
      echo "1. Install flyctl: curl -L https://fly.io/install.sh | sh"
      echo "2. Run: fly launch --image ${FULL_IMAGE_NAME}"
      ;;
    aws)
      echo "For AWS ECS deployment:"
      echo "1. Create an ECS cluster and task definition"
      echo "2. Run: aws ecs update-service --cluster your-cluster --service your-service --force-new-deployment"
      ;;
    azure)
      echo "For Azure Container Instances deployment:"
      echo "1. Run: az container create --resource-group myResourceGroup --name ai-orchestra --image ${FULL_IMAGE_NAME} --dns-name-label ai-orchestra --ports 8080"
      ;;
    digital-ocean)
      echo "For Digital Ocean App Platform deployment:"
      echo "1. Create an app from the Digital Ocean dashboard"
      echo "2. Select 'Docker Hub' as the source"
      echo "3. Enter the image name: ${FULL_IMAGE_NAME}"
      ;;
    *)
      echo -e "${RED}Unknown deployment target: ${DEPLOY_TARGET}${NC}"
      echo "Supported targets: render, fly, aws, azure, digital-ocean"
      exit 1
      ;;
  esac
else
  echo -e "${YELLOW}Image built and pushed successfully.${NC}"
  echo -e "${YELLOW}To deploy, specify a target platform with --target.${NC}"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${GREEN}Your application is ready to be deployed with hardcoded GCP authentication.${NC}"
echo -e "${GREEN}No additional authentication or configuration is needed.${NC}"
