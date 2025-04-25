#!/bin/bash
# deploy_to_cloud_run.sh
#
# This script automates the deployment of the Orchestra API to Cloud Run
# using the enhanced configuration from our Terraform infrastructure.
#
# Usage:
#   ./deploy_to_cloud_run.sh [ENV]
#
# Where ENV is one of: dev, stage, prod (defaults to dev if not specified)

set -e

# Default values
ENV=${1:-dev}
REGION="us-central1"
PROJECT_ID="agi-baby-cherry"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Orchestra API Deployment to Cloud Run (${ENV})      ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Validate environment argument
if [[ ! "$ENV" =~ ^(dev|stage|prod)$ ]]; then
    echo -e "${RED}Error: Environment must be one of: dev, stage, prod${NC}"
    exit 1
fi

# Set environment-specific variables
if [ "$ENV" == "prod" ]; then
    MIN_INSTANCES=1
    MAX_INSTANCES=20
    MEMORY="4Gi"
    CPU=2
elif [ "$ENV" == "stage" ]; then
    MIN_INSTANCES=1
    MAX_INSTANCES=10
    MEMORY="2Gi"
    CPU=1
else
    MIN_INSTANCES=0
    MAX_INSTANCES=5
    MEMORY="2Gi"
    CPU=1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it and try again.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install it and try again.${NC}"
    exit 1
fi

# Check authentication
echo -e "${YELLOW}Checking GCP authentication...${NC}"
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$ACCOUNT" ]; then
    echo -e "${RED}Error: Not authenticated to Google Cloud. Run 'gcloud auth login' and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}Authenticated as: $ACCOUNT${NC}"

# Set project
echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Check if necessary APIs are enabled
echo -e "${YELLOW}Checking if necessary APIs are enabled...${NC}"
APIS=("run.googleapis.com" "artifactregistry.googleapis.com" "secretmanager.googleapis.com")
for API in "${APIS[@]}"; do
    if ! gcloud services list --enabled --filter="name:$API" | grep -q "$API"; then
        echo -e "${YELLOW}Enabling $API...${NC}"
        gcloud services enable $API
    fi
done

# Build versioned image
VERSION=$(git rev-parse --short HEAD || echo "latest")
BUILD_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/orchestra/orchestrator:${ENV}-${VERSION}"

echo -e "${YELLOW}Building Docker image: $IMAGE_NAME${NC}"
docker build \
  --build-arg ENV=$ENV \
  --build-arg VERSION=$VERSION \
  --build-arg BUILD_TIME=$BUILD_TIME \
  -t $IMAGE_NAME .

# Push to Artifact Registry
echo -e "${YELLOW}Configuring Docker for GCP Artifact Registry...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo -e "${YELLOW}Pushing image to Artifact Registry...${NC}"
docker push $IMAGE_NAME

# Get VPC connector name
echo -e "${YELLOW}Getting VPC connector name...${NC}"
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list \
  --filter="name:orchestrator-vpc-connector-${ENV}" \
  --format="value(name)" --limit=1)

if [ -z "$VPC_CONNECTOR" ]; then
  echo -e "${RED}Warning: VPC connector not found. Deployment will proceed without VPC connector.${NC}"
  VPC_CONNECTOR_ARG=""
else
  VPC_CONNECTOR_ARG="--vpc-connector=$VPC_CONNECTOR --vpc-egress=private-ranges-only"
fi

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy orchestrator-api-${ENV} \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=$MIN_INSTANCES \
  --max-instances=$MAX_INSTANCES \
  --cpu=$CPU \
  --memory=$MEMORY \
  $VPC_CONNECTOR_ARG \
  --set-env-vars="ENVIRONMENT=${ENV},LOG_LEVEL=${ENV == 'prod' ? 'INFO' : 'DEBUG'}"

# Get deployment URL
SERVICE_URL=$(gcloud run services describe orchestrator-api-${ENV} \
  --region=$REGION \
  --format='value(status.url)')

# Perform health check
echo -e "${YELLOW}Performing health check...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/api/health)

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo -e "${GREEN}Health check successful: $HTTP_STATUS${NC}"
else
  echo -e "${RED}Health check failed with status: $HTTP_STATUS${NC}"
  echo -e "${YELLOW}Service may still be starting up. Check logs for more details.${NC}"
fi

# Display summary
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Deployment Summary                                 ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Environment:${NC} $ENV"
echo -e "${GREEN}Region:${NC} $REGION"
echo -e "${GREEN}Version:${NC} $VERSION"
echo -e "${GREEN}Service URL:${NC} $SERVICE_URL"
echo -e "${GREEN}Service Account:${NC} $(gcloud run services describe orchestrator-api-${ENV} --region=$REGION --format='value(spec.template.spec.serviceAccountName)')"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}To view logs: ${NC}gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-${ENV}' --limit=10"
echo -e "${YELLOW}To view metrics: ${NC}https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo -e "${BLUE}======================================================${NC}"
