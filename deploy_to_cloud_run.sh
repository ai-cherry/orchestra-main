#!/bin/bash
# deploy_to_cloud_run.sh
# Script to deploy the AI Orchestra API to Google Cloud Run

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="orchestra-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if GCP_MASTER_SERVICE_JSON environment variable is set
if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
  log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is not set. Please set it and try again."
  exit 1
fi

# Create temporary service account key file from environment variable
log "INFO" "Creating temporary service account key file from GCP_MASTER_SERVICE_JSON..."
echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/gcp-credentials.json
chmod 600 /tmp/gcp-credentials.json

# Set environment variable for authentication
log "INFO" "Setting GOOGLE_APPLICATION_CREDENTIALS environment variable..."
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-credentials.json

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  log "ERROR" "gcloud is required but not installed. Please install it and try again."
  log "INFO" "You can install gcloud by following the instructions at: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Authenticate with GCP
log "INFO" "Authenticating with GCP..."
gcloud auth activate-service-account --key-file=/tmp/gcp-credentials.json

# Set the project ID
log "INFO" "Setting project ID to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build the Docker image
log "INFO" "Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push the Docker image to Google Container Registry
log "INFO" "Pushing Docker image to Google Container Registry..."
gcloud auth configure-docker -q
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
log "INFO" "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION},ENVIRONMENT=prod" \
  --service-account="orchestra-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform=managed --region=${REGION} --format="value(status.url)")

# Cleanup
log "INFO" "Cleaning up..."
rm -f /tmp/gcp-credentials.json

log "SUCCESS" "Deployment completed successfully!"
log "INFO" "Your API is now available at: ${SERVICE_URL}"
log "INFO" "You can test it by visiting: ${SERVICE_URL}/docs"
