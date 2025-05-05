#!/bin/bash
# Script to build a Docker image and deploy to Cloud Run
# Uses the authenticated GCP service account credentials

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables
GCP_PROJECT_ID="cherry-ai-project"
DOCKER_IMAGE_NAME="orchestrator-api"
DOCKER_TAG="latest"
CLOUD_RUN_SERVICE_NAME="orchestrator-api"
REGION="us-central1"

# Print header
echo -e "${BLUE}${BOLD}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   DOCKER BUILD AND CLOUD RUN DEPLOYMENT SCRIPT   ${NC}"
echo -e "${BLUE}${BOLD}=================================================================${NC}"

# Check for required tools
check_requirements() {
  echo -e "${YELLOW}Checking requirements...${NC}"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for docker
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is required but not found.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}All required tools are installed.${NC}"
}

# Verify GCP authentication
verify_gcp_auth() {
  echo -e "${YELLOW}Verifying GCP authentication...${NC}"
  
  # Check if authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GCP. Please run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  
  # Set project
  gcloud config set project "$GCP_PROJECT_ID"
  
  echo -e "${GREEN}GCP authentication verified and project set to: $GCP_PROJECT_ID${NC}"
}

# Build Docker image
build_docker_image() {
  echo -e "${YELLOW}Building Docker image: ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}...${NC}"
  
  # Check if Dockerfile exists
  if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found in the current directory.${NC}"
    exit 1
  fi
  
  # Build Docker image
  docker build -t "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}" .
  
  echo -e "${GREEN}Docker image built successfully.${NC}"
}

# Push Docker image to Google Container Registry
push_to_gcr() {
  echo -e "${YELLOW}Pushing Docker image to Google Container Registry...${NC}"
  
  # Tag the Docker image for GCR
  local gcr_image="gcr.io/${GCP_PROJECT_ID}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
  docker tag "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}" "$gcr_image"
  
  # Push to GCR
  gcloud builds submit --tag "$gcr_image" .
  
  echo -e "${GREEN}Docker image pushed to GCR: $gcr_image${NC}"
  
  # Return the GCR image name
  echo "$gcr_image"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
  local image=$1
  
  echo -e "${YELLOW}Deploying to Cloud Run: ${CLOUD_RUN_SERVICE_NAME}...${NC}"
  
  # Deploy to Cloud Run
  gcloud run deploy "$CLOUD_RUN_SERVICE_NAME" \
    --image="$image" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --project="$GCP_PROJECT_ID"
  
  echo -e "${GREEN}Deployed to Cloud Run successfully.${NC}"
  
  # Get the Cloud Run URL
  local url=$(gcloud run services describe "$CLOUD_RUN_SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --format="value(status.url)" \
    --project="$GCP_PROJECT_ID")
  
  echo -e "${GREEN}Cloud Run URL: $url${NC}"
}

# Parse command line arguments
parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case $1 in
      --project-id) GCP_PROJECT_ID="$2"; shift ;;
      --image-name) DOCKER_IMAGE_NAME="$2"; shift ;;
      --tag) DOCKER_TAG="$2"; shift ;;
      --service-name) CLOUD_RUN_SERVICE_NAME="$2"; shift ;;
      --region) REGION="$2"; shift ;;
      *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
  done
}

# Main function
main() {
  # Parse command line arguments
  parse_args "$@"
  
  # Check requirements
  check_requirements
  
  # Verify GCP authentication
  verify_gcp_auth
  
  # Build Docker image
  build_docker_image
  
  # Push to GCR
  local gcr_image=$(push_to_gcr)
  
  # Deploy to Cloud Run
  deploy_to_cloud_run "$gcr_image"
  
  echo -e "\n${GREEN}${BOLD}Deployment to Cloud Run completed successfully!${NC}"
  echo -e "${YELLOW}You can now access your service at the URL shown above.${NC}"
}

# Execute main function with arguments
main "$@"
