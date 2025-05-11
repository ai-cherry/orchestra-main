#!/bin/bash
# deploy_optimized.sh - Performance-optimized deployment script for MCP Server
# 
# This script automates the deployment of the MCP server to Google Cloud Platform
# with performance-optimized settings. It handles authentication, builds the Docker
# image, and deploys to Cloud Run with appropriate scaling and resource settings.

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
SERVICE_NAME="mcp-server"
MIN_INSTANCES=1
MAX_INSTANCES=100
CPU=2
MEMORY="2Gi"
CONCURRENCY=80
TIMEOUT="300s"
VPC_CONNECTOR="vpc-connector"
REDIS_INSTANCE="mcp-redis"
REDIS_TIER="STANDARD_HA"
REDIS_SIZE_GB=10
REDIS_VERSION="REDIS_6_X"

# Display banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                 MCP Server Optimized Deployment                ║"
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
    --service-name)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --min-instances)
      MIN_INSTANCES="$2"
      shift 2
      ;;
    --max-instances)
      MAX_INSTANCES="$2"
      shift 2
      ;;
    --cpu)
      CPU="$2"
      shift 2
      ;;
    --memory)
      MEMORY="$2"
      shift 2
      ;;
    --concurrency)
      CONCURRENCY="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --vpc-connector)
      VPC_CONNECTOR="$2"
      shift 2
      ;;
    --redis-instance)
      REDIS_INSTANCE="$2"
      shift 2
      ;;
    --redis-tier)
      REDIS_TIER="$2"
      shift 2
      ;;
    --redis-size)
      REDIS_SIZE_GB="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project PROJECT_ID       GCP project ID (default: cherry-ai-project)"
      echo "  --region REGION            GCP region (default: us-central1)"
      echo "  --service-name NAME        Cloud Run service name (default: mcp-server)"
      echo "  --min-instances N          Minimum instances (default: 1)"
      echo "  --max-instances N          Maximum instances (default: 100)"
      echo "  --cpu N                    CPU count (default: 2)"
      echo "  --memory SIZE              Memory size (default: 2Gi)"
      echo "  --concurrency N            Concurrency per instance (default: 80)"
      echo "  --timeout DURATION         Request timeout (default: 300s)"
      echo "  --vpc-connector NAME       VPC connector name (default: vpc-connector)"
      echo "  --redis-instance NAME      Redis instance name (default: mcp-redis)"
      echo "  --redis-tier TIER          Redis tier (default: STANDARD_HA)"
      echo "  --redis-size SIZE_GB       Redis size in GB (default: 10)"
      echo "  --help                     Display this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $key${NC}"
      exit 1
      ;;
  esac
done

# Check for required environment variables
if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
  echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable is not set.${NC}"
  echo "Please set it to the content of your GCP service account key JSON."
  exit 1
fi

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

# Authenticate with GCP
step "Authenticating with Google Cloud Platform"
echo "$GCP_MASTER_SERVICE_JSON" > /tmp/gcp-key.json
gcloud auth activate-service-account --key-file=/tmp/gcp-key.json || error "Failed to authenticate with GCP"
gcloud config set project "$PROJECT_ID" || error "Failed to set GCP project"
info "Successfully authenticated with GCP"

# Set up Docker configuration
step "Setting up Docker configuration"
gcloud auth configure-docker --quiet || warn "Docker configuration might not be complete"

# Generate a unique build ID
BUILD_ID=$(date +%Y%m%d%H%M%S)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_ID"

# Build the Docker image
step "Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f Dockerfile . || error "Docker build failed"
info "Docker image built successfully"

# Push the Docker image to Google Container Registry
step "Pushing Docker image to Google Container Registry"
docker push "$IMAGE_NAME" || error "Failed to push Docker image"
info "Docker image pushed successfully"

# Set up Redis if it doesn't exist
step "Setting up Redis instance"
if ! gcloud redis instances describe "$REDIS_INSTANCE" --region="$REGION" &>/dev/null; then
  info "Creating Redis instance: $REDIS_INSTANCE"
  gcloud redis instances create "$REDIS_INSTANCE" \
    --region="$REGION" \
    --tier="$REDIS_TIER" \
    --size="$REDIS_SIZE_GB" \
    --redis-version="$REDIS_VERSION" \
    --redis-config="maxmemory-policy=volatile-lru,notify-keyspace-events=KEA,timeout=3600" || warn "Failed to create Redis instance, deployment will continue but may not function correctly"
else
  info "Redis instance $REDIS_INSTANCE already exists"
fi

# Get Redis host and port
REDIS_HOST=$(gcloud redis instances describe "$REDIS_INSTANCE" --region="$REGION" --format="value(host)")
REDIS_PORT=$(gcloud redis instances describe "$REDIS_INSTANCE" --region="$REGION" --format="value(port)")

# Create secrets if they don't exist
step "Setting up Secret Manager secrets"
# Check if the secret exists
if ! gcloud secrets describe "redis-credentials" &>/dev/null; then
  info "Creating redis-credentials secret"
  echo "{\"host\":\"$REDIS_HOST\",\"port\":$REDIS_PORT}" | gcloud secrets create "redis-credentials" --data-file=- --replication-policy="automatic"
else
  info "Secret redis-credentials already exists"
fi

# Deploy to Cloud Run
step "Deploying to Cloud Run"
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE_NAME" \
  --region="$REGION" \
  --platform="managed" \
  --cpu="$CPU" \
  --memory="$MEMORY" \
  --concurrency="$CONCURRENCY" \
  --timeout="$TIMEOUT" \
  --min-instances="$MIN_INSTANCES" \
  --max-instances="$MAX_INSTANCES" \
  --vpc-connector="projects/$PROJECT_ID/locations/$REGION/connectors/$VPC_CONNECTOR" \
  --set-secrets="REDIS_CREDENTIALS=redis-credentials:latest" \
  --allow-unauthenticated || error "Failed to deploy to Cloud Run"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

# Clean up temporary files
rm -f /tmp/gcp-key.json

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Deployment Successful!                      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo -e "${BLUE}Service URL: ${NC}$SERVICE_URL"
echo -e "${BLUE}Project ID: ${NC}$PROJECT_ID"
echo -e "${BLUE}Region: ${NC}$REGION"
echo -e "${BLUE}Redis Host: ${NC}$REDIS_HOST"
echo -e "${BLUE}Redis Port: ${NC}$REDIS_PORT"
echo ""
echo -e "${YELLOW}To monitor the service, visit:${NC}"
echo -e "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"