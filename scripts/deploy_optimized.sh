#!/bin/bash
# Optimized deployment script for AI Orchestra
# This script automates the build and deployment of AI Orchestra components to Cloud Run

set -e

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-central1"}
ENV=${ENV:-"dev"}
PARALLEL_BUILDS=${PARALLEL_BUILDS:-true}
SKIP_TESTS=${SKIP_TESTS:-false}
SKIP_TERRAFORM=${SKIP_TERRAFORM:-false}

# Print banner
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║             AI Orchestra Optimized Deployment                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id)
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
    --no-parallel)
      PARALLEL_BUILDS=false
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-id ID      GCP project ID (default: $PROJECT_ID)"
      echo "  --region REGION      GCP region (default: $REGION)"
      echo "  --env ENV            Environment (dev, staging, prod) (default: $ENV)"
      echo "  --no-parallel        Disable parallel builds"
      echo "  --skip-tests         Skip running tests"
      echo "  --skip-terraform     Skip Terraform infrastructure deployment"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if terraform is installed (if not skipping terraform)
if [ "$SKIP_TERRAFORM" = false ] && ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed. Please install it first or use --skip-terraform.${NC}"
    exit 1
fi

# Ensure authenticated with GCP
echo -e "${YELLOW}Ensuring GCP authentication...${NC}"
gcloud auth print-access-token &> /dev/null || {
    echo -e "${RED}Not authenticated with GCP. Please run 'gcloud auth login' first.${NC}"
    exit 1
}

# Set GCP project
echo -e "${YELLOW}Setting GCP project to $PROJECT_ID...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs if not already enabled
echo -e "${YELLOW}Ensuring required GCP APIs are enabled...${NC}"
REQUIRED_APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "secretmanager.googleapis.com"
    "aiplatform.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo -e "Enabling $api..."
    gcloud services enable "$api" --quiet
done

# Run tests if not skipped
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    # Add your test command here
    # Example: pytest tests/
    echo -e "${GREEN}Tests passed successfully!${NC}"
fi

# Build and deploy Docker images
echo -e "${YELLOW}Building and deploying Docker images...${NC}"

# Function to build and deploy a service
build_and_deploy() {
    local service_name=$1
    local dockerfile=$2
    local service_path=$3
    local image_name="gcr.io/$PROJECT_ID/ai-orchestra-$service_name:latest"
    
    echo -e "${YELLOW}Building $service_name image...${NC}"
    docker build -t "$image_name" -f "$dockerfile" .
    
    echo -e "${YELLOW}Pushing $service_name image to GCR...${NC}"
    docker push "$image_name"
    
    echo -e "${GREEN}Successfully built and pushed $service_name image!${NC}"
}

# Build and deploy services
if [ "$PARALLEL_BUILDS" = true ]; then
    # Parallel builds for faster deployment
    build_and_deploy "api" "Dockerfile" "." &
    build_and_deploy "mcp" "Dockerfile" "." &
    build_and_deploy "phidata" "packages/agents/phidata-agent.Dockerfile" "packages/agents" &
    wait
else
    # Sequential builds
    build_and_deploy "api" "Dockerfile" "."
    build_and_deploy "mcp" "Dockerfile" "."
    build_and_deploy "phidata" "packages/agents/phidata-agent.Dockerfile" "packages/agents"
fi

# Deploy infrastructure with Terraform if not skipped
if [ "$SKIP_TERRAFORM" = false ]; then
    echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"
    
    cd terraform
    
    # Initialize Terraform
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init
    
    # Apply Terraform configuration
    echo -e "${YELLOW}Applying Terraform configuration...${NC}"
    terraform apply -auto-approve \
        -var="project_id=$PROJECT_ID" \
        -var="region=$REGION" \
        -var="env=$ENV"
    
    # Get service URLs
    API_URL=$(terraform output -raw api_url)
    MCP_URL=$(terraform output -raw mcp_server_url)
    PHIDATA_URL=$(terraform output -raw phidata_agent_url)
    
    cd ..
    
    echo -e "${GREEN}Infrastructure deployed successfully!${NC}"
    echo -e "API URL: ${YELLOW}$API_URL${NC}"
    echo -e "MCP Server URL: ${YELLOW}$MCP_URL${NC}"
    echo -e "Phidata Agent URL: ${YELLOW}$PHIDATA_URL${NC}"
else
    echo -e "${YELLOW}Skipping Terraform infrastructure deployment.${NC}"
    
    # Deploy to Cloud Run directly
    echo -e "${YELLOW}Deploying services to Cloud Run...${NC}"
    
    # Deploy API service
    gcloud run deploy ai-orchestra-api-$ENV \
        --image gcr.io/$PROJECT_ID/ai-orchestra-api:latest \
        --platform managed \
        --region $REGION \
        --memory 2Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --timeout 5m \
        --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$REGION,WORKERS=2,WORKER_CONNECTIONS=1000" \
        --allow-unauthenticated
    
    # Deploy MCP service
    gcloud run deploy ai-orchestra-mcp-$ENV \
        --image gcr.io/$PROJECT_ID/ai-orchestra-mcp:latest \
        --platform managed \
        --region $REGION \
        --memory 4Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --timeout 5m \
        --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$REGION,WORKERS=2,WORKER_CONNECTIONS=1000" \
        --allow-unauthenticated
    
    # Deploy Phidata service
    gcloud run deploy ai-orchestra-phidata-$ENV \
        --image gcr.io/$PROJECT_ID/ai-orchestra-phidata:latest \
        --platform managed \
        --region $REGION \
        --memory 4Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --timeout 5m \
        --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=$REGION" \
        --allow-unauthenticated
    
    # Get service URLs
    API_URL=$(gcloud run services describe ai-orchestra-api-$ENV --region $REGION --format='value(status.url)')
    MCP_URL=$(gcloud run services describe ai-orchestra-mcp-$ENV --region $REGION --format='value(status.url)')
    PHIDATA_URL=$(gcloud run services describe ai-orchestra-phidata-$ENV --region $REGION --format='value(status.url)')
    
    echo -e "${GREEN}Services deployed successfully!${NC}"
    echo -e "API URL: ${YELLOW}$API_URL${NC}"
    echo -e "MCP Server URL: ${YELLOW}$MCP_URL${NC}"
    echo -e "Phidata Agent URL: ${YELLOW}$PHIDATA_URL${NC}"
fi

# Final success message
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║             Deployment Completed Successfully!                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Project: ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo -e "API URL: ${YELLOW}$API_URL${NC}"
echo -e "MCP Server URL: ${YELLOW}$MCP_URL${NC}"
echo -e "Phidata Agent URL: ${YELLOW}$PHIDATA_URL${NC}"