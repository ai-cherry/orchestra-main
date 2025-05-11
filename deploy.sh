#!/bin/bash
# deploy.sh - Simplified deployment script for AI Orchestra project
# 
# This script automates the deployment of the entire AI Orchestra project to Google Cloud Platform
# It handles dependency resolution, authentication, and deployment of all components

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
ENV="dev"

# Display banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                 AI Orchestra Deployment Script                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project PROJECT_ID       GCP project ID (default: cherry-ai-project)"
      echo "  --region REGION            GCP region (default: us-central1)"
      echo "  --env ENV                  Environment (dev, staging, prod) (default: dev)"
      echo "  --help                     Display this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $key${NC}"
      exit 1
      ;;
  esac
done

# Function to display step information
step() {
  echo -e "${GREEN}➤ $1${NC}"
}

# Function to display information
info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

# Function to display warnings
warn() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to display errors and exit
error() {
  echo -e "${RED}✖ $1${NC}"
  exit 1
}

# Function to prompt for confirmation
confirm() {
  local message=$1
  local response
  
  echo -e "${YELLOW}${message} (y/n)${NC}"
  read -r response
  
  if [[ "$response" =~ ^[Yy]$ ]]; then
    return 0  # true
  else
    return 1  # false
  fi
}

# Check for required environment variables
if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
  echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable is not set.${NC}"
  echo "Please set it to the content of your GCP service account key JSON."
  exit 1
fi

# Step 1: Fix dependencies and update Poetry
step "Fixing dependencies and updating Poetry"

cd mcp_server
info "Updating Poetry dependencies"
poetry update || error "Failed to update Poetry dependencies"
cd ..

# Step 2: Authenticate with GCP
step "Authenticating with Google Cloud Platform"
echo "$GCP_MASTER_SERVICE_JSON" > /tmp/gcp-key.json
gcloud auth activate-service-account --key-file=/tmp/gcp-key.json || error "Failed to authenticate with GCP"
gcloud config set project "$PROJECT_ID" || error "Failed to set GCP project"
info "Successfully authenticated with GCP"

# Step 3: Enable required APIs
step "Enabling required APIs"
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  workstations.googleapis.com \
  compute.googleapis.com \
  --project="$PROJECT_ID" || warn "Failed to enable some APIs, deployment may not be complete"

# Step 4: Apply Terraform
step "Applying Terraform configuration"

if confirm "Do you want to apply Terraform configuration?"; then
  cd terraform
  
  # Initialize Terraform
  info "Initializing Terraform"
  terraform init || error "Failed to initialize Terraform"
  
  # Plan Terraform changes
  info "Planning Terraform changes"
  terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="env=$ENV" -out=tfplan || error "Failed to plan Terraform changes"
  
  # Apply Terraform changes
  info "Applying Terraform changes"
  terraform apply tfplan || error "Failed to apply Terraform changes"
  
  cd ..
else
  warn "Skipping Terraform apply"
fi

# Step 5: Build and deploy MCP Server
step "Building and deploying MCP Server"

if confirm "Do you want to build and deploy the MCP Server?"; then
  cd mcp_server
  
  # Make the deployment script executable
  chmod +x deploy/deploy_optimized.sh
  
  # Run the deployment script
  ./deploy/deploy_optimized.sh \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --service-name "mcp-server-$ENV" || error "Failed to deploy MCP Server"
  
  cd ..
else
  warn "Skipping MCP Server deployment"
fi

# Step 6: Build and deploy main application
step "Building and deploying main application"

if confirm "Do you want to build and deploy the main application?"; then
  # Set up Docker configuration
  info "Setting up Docker configuration"
  gcloud auth configure-docker --quiet || warn "Docker configuration might not be complete"
  
  # Generate a unique build ID
  BUILD_ID=$(date +%Y%m%d%H%M%S)
  IMAGE_NAME="gcr.io/$PROJECT_ID/orchestra-api:$BUILD_ID"
  
  # Build the Docker image
  info "Building Docker image: $IMAGE_NAME"
  docker build -t "$IMAGE_NAME" . || error "Docker build failed"
  info "Docker image built successfully"
  
  # Push the Docker image to Google Container Registry
  info "Pushing Docker image to Google Container Registry"
  docker push "$IMAGE_NAME" || error "Failed to push Docker image"
  info "Docker image pushed successfully"
  
  # Deploy to Cloud Run
  info "Deploying to Cloud Run"
  gcloud run deploy "orchestra-api-$ENV" \
    --image="$IMAGE_NAME" \
    --region="$REGION" \
    --platform="managed" \
    --memory="2Gi" \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300s \
    --service-account="orchestra-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,ENVIRONMENT=$ENV,REGION=$REGION" \
    --allow-unauthenticated || error "Failed to deploy to Cloud Run"
  
  # Get the service URL
  SERVICE_URL=$(gcloud run services describe "orchestra-api-$ENV" --region="$REGION" --format="value(status.url)")
  info "Service URL: $SERVICE_URL"
else
  warn "Skipping main application deployment"
fi

# Clean up temporary files
rm -f /tmp/gcp-key.json

# Completion message
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Deployment Successful!                      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo -e "${BLUE}Project ID: ${NC}$PROJECT_ID"
echo -e "${BLUE}Region: ${NC}$REGION"
echo -e "${BLUE}Environment: ${NC}$ENV"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Verify the deployed infrastructure is working as expected"
echo -e "2. Set up Workload Identity Federation for improved security"
echo -e "3. Delete any local copies of service account keys for security"
echo ""
echo -e "${GREEN}Thank you for using the AI Orchestra deployment script!${NC}"
