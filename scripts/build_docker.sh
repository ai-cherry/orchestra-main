#!/bin/bash
# build_docker.sh - Build Docker images for different services with appropriate Python versions

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
SERVICE="core"
TAG="latest"
PUSH=false
PROJECT_ID="cherry-ai-project"
REGION="us-west4"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --service|-s)
      SERVICE="$2"
      shift
      shift
      ;;
    --tag|-t)
      TAG="$2"
      shift
      shift
      ;;
    --push|-p)
      PUSH=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --service, -s   Service to build (core, ingestion, llm-test, phidata) [default: core]"
      echo "  --tag, -t       Docker image tag [default: latest]"
      echo "  --push, -p      Push to GCR after building"
      echo "  --help, -h      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set target stage based on service
case $SERVICE in
  core)
    TARGET="python311"
    ;;
  ingestion)
    TARGET="python310"
    ;;
  llm-test)
    TARGET="python311"
    ;;
  phidata)
    TARGET="python311"
    ;;
  *)
    echo -e "${RED}Error: Unknown service '$SERVICE'${NC}"
    exit 1
    ;;
esac

# Build the Docker image
echo -e "${YELLOW}Building Docker image for $SERVICE service (Python target: $TARGET)...${NC}"
IMAGE_NAME="orchestra-$SERVICE:$TAG"

# Use BuildKit for better performance and multi-stage builds
export DOCKER_BUILDKIT=1
docker build --target $TARGET -t $IMAGE_NAME .

echo -e "${GREEN}Docker image built successfully: $IMAGE_NAME${NC}"

# Push to GCR if requested
if [ "$PUSH" = true ]; then
  GCR_IMAGE="gcr.io/$PROJECT_ID/$IMAGE_NAME"
  echo -e "${YELLOW}Tagging and pushing to GCR: $GCR_IMAGE${NC}"
  
  # Tag the image for GCR
  docker tag $IMAGE_NAME $GCR_IMAGE
  
  # Push to GCR
  docker push $GCR_IMAGE
  
  echo -e "${GREEN}Image pushed to GCR: $GCR_IMAGE${NC}"
fi

echo -e "${GREEN}Done!${NC}"