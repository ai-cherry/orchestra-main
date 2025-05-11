Z#!/bin/bash
# quick_deploy.sh - Script to quickly deploy the MCP server to GCP
# Uses the already authenticated service account

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting quick deployment of MCP server to GCP...${NC}"

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="mcp-server"
ENV=${1:-"dev"}  # Default to dev environment if not specified
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}-${ENV}"

# Function to update Poetry dependencies
update_dependencies() {
    echo -e "${YELLOW}Updating Poetry dependencies...${NC}"
    poetry update
}

# Function to build Docker image
build_docker_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    
    # Build the Docker image
    docker build -t ${IMAGE_NAME} -f Dockerfile.optimized ..
    
    # Push the Docker image to Google Container Registry
    echo -e "${YELLOW}Pushing Docker image to Google Container Registry...${NC}"
    gcloud auth configure-docker gcr.io --quiet
    docker push ${IMAGE_NAME}
}

# Function to deploy to Cloud Run
deploy_to_cloud_run() {
    echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
    
    # Deploy to Cloud Run
    gcloud run deploy ${SERVICE_NAME}-${ENV} \
        --image=${IMAGE_NAME} \
        --platform=managed \
        --region=${REGION} \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --concurrency=80 \
        --timeout=300s \
        --set-env-vars="ENV=${ENV},PROJECT_ID=${PROJECT_ID}"
    
    # Get the deployed service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME}-${ENV} --platform=managed --region=${REGION} --format='value(status.url)')
    
    echo -e "${GREEN}MCP server deployed successfully!${NC}"
    echo -e "Service URL: ${SERVICE_URL}"
}

# Main execution
main() {
    # Update dependencies
    update_dependencies
    
    # Build Docker image
    build_docker_image
    
    # Deploy to Cloud Run
    deploy_to_cloud_run
}

# Run the main function
main