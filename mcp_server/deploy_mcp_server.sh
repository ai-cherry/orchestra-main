#!/bin/bash
# deploy_mcp_server.sh - Script to deploy the MCP server to GCP
# Uses the configured credentials to build and deploy the application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of MCP server to GCP...${NC}"

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="mcp-server"
ENV=${1:-"dev"}  # Default to dev environment if not specified

# Create temporary directory for credentials
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Function to set up GCP credentials
setup_gcp_credentials() {
    echo -e "${YELLOW}Setting up GCP credentials...${NC}"
    
    # Check if GCP_PROJECT_ADMIN_KEY is set
    if [ -z "${GCP_PROJECT_ADMIN_KEY}" ]; then
        echo -e "${RED}Error: GCP_PROJECT_ADMIN_KEY environment variable is not set.${NC}"
        echo "Please set the GCP_PROJECT_ADMIN_KEY environment variable with your GCP project admin key."
        exit 1
    fi
    
    # Save credentials to temporary file
    echo "${GCP_PROJECT_ADMIN_KEY}" > "${TEMP_DIR}/project-admin-key.json"
    chmod 600 "${TEMP_DIR}/project-admin-key.json"
    
    # Authenticate with gcloud using project admin key
    echo -e "${YELLOW}Authenticating with Google Cloud using project admin key...${NC}"
    gcloud auth activate-service-account --key-file="${TEMP_DIR}/project-admin-key.json"
    gcloud config set project ${PROJECT_ID}
}

# Function to update Poetry dependencies
update_dependencies() {
    echo -e "${YELLOW}Updating Poetry dependencies...${NC}"
    poetry update
}

# Function to build Docker image
build_docker_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    
    # Build the Docker image
    IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}-${ENV}"
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
    # Set up GCP credentials
    setup_gcp_credentials
    
    # Update dependencies
    update_dependencies
    
    # Build Docker image
    build_docker_image
    
    # Deploy to Cloud Run
    deploy_to_cloud_run
}

# Run the main function
main