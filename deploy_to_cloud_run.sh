#!/bin/bash
# Deployment script for FastAPI backend to Cloud Run
# This script automates the steps from docs/cloud_run_deployment.md

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="agi-baby-cherry"
REGION="us-west2"
IMAGE_NAME="orchestrator"
ENV="dev"

echo -e "${BLUE}====== Orchestra FastAPI Deployment to Cloud Run ======${NC}"

# Step 1: Authenticate with Google Cloud
echo -e "\n${GREEN}Step 1: Authenticating with Google Cloud...${NC}"

# Check if already authenticated
if ! gcloud auth print-access-token &>/dev/null; then
  echo -e "${YELLOW}Not authenticated. Please log in:${NC}"
  gcloud auth login
else
  echo -e "${GREEN}Already authenticated with Google Cloud.${NC}"
fi

# Configure Docker for Artifact Registry
echo -e "\n${GREEN}Configuring Docker for Artifact Registry...${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# Set project and region
echo -e "\n${GREEN}Setting default project and region...${NC}"
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Step 2: Build the Docker image
echo -e "\n${GREEN}Step 2: Building Docker image...${NC}"
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/orchestra/$IMAGE_NAME:$ENV-latest"
echo -e "${YELLOW}Building image: $IMAGE_TAG${NC}"

docker build -t $IMAGE_TAG .

# Step 3: Push to Artifact Registry
echo -e "\n${GREEN}Step 3: Pushing image to Artifact Registry...${NC}"

# Check if repository exists, create if not
if ! gcloud artifacts repositories describe orchestra --location=$REGION &>/dev/null; then
  echo -e "${YELLOW}Creating Artifact Registry repository 'orchestra'...${NC}"
  gcloud artifacts repositories create orchestra \
    --repository-format=docker \
    --location=$REGION \
    --description="Orchestra Docker images"
else
  echo -e "${GREEN}Artifact Registry repository 'orchestra' already exists.${NC}"
fi

echo -e "${YELLOW}Pushing image: $IMAGE_TAG${NC}"
docker push $IMAGE_TAG

# Step 4: Deploy with Terraform
echo -e "\n${GREEN}Step 4: Deploying to Cloud Run using Terraform...${NC}"
cd infra/dev

echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

echo -e "${YELLOW}Selecting workspace...${NC}"
terraform workspace select $ENV || terraform workspace new $ENV

echo -e "${YELLOW}Applying Terraform configuration...${NC}"
terraform apply -var="env=$ENV"

# Step 5: Verify deployment
echo -e "\n${GREEN}Step 5: Verifying deployment...${NC}"
SERVICE_URL=$(gcloud run services describe orchestrator-api-$ENV --region=$REGION --format="value(status.url)")

echo -e "${YELLOW}Waiting for service to be ready...${NC}"
sleep 10  # Give some time for the service to be ready

echo -e "${YELLOW}Testing service health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s $SERVICE_URL/health)
echo "Response from health endpoint: $HEALTH_RESPONSE"

# Step 6: Show logs
echo -e "\n${GREEN}Step 6: Showing recent logs...${NC}"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-$ENV" --limit=5

echo -e "\n${BLUE}====== Deployment Complete ======${NC}"
echo -e "${GREEN}Your FastAPI service is now running at: ${YELLOW}$SERVICE_URL${NC}"
echo -e "${GREEN}To view more logs, run:${NC}"
echo -e "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-$ENV\" --limit=10"
