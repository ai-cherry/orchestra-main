#!/bin/bash
# test_gcp_deployment.sh
# Script to test GCP deployment and verify that resources have been successfully provisioned

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
ZONE="us-central1-a"
SERVICE_NAME="orchestra-api"

# Ensure GCP environment variables are set
log "INFO" "Ensuring GCP environment variables are set..."
source ./ensure_gcp_env.sh

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  log "ERROR" "gcloud is required but not installed. Please install it and try again."
  log "INFO" "You can install gcloud by following the instructions at: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Verify gcloud configuration
log "INFO" "Verifying gcloud configuration..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)

if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
  log "WARN" "gcloud project is not set correctly. Current project: $CURRENT_PROJECT"
  log "INFO" "Setting project to $PROJECT_ID..."
  gcloud config set project $PROJECT_ID
else
  log "SUCCESS" "gcloud project is correctly set to $PROJECT_ID"
fi

if [ "$CURRENT_ACCOUNT" != "scoobyjava@cherry-ai.me" ]; then
  log "WARN" "gcloud account is not set correctly. Current account: $CURRENT_ACCOUNT"
  log "INFO" "Setting account to scoobyjava@cherry-ai.me..."
  gcloud config set account scoobyjava@cherry-ai.me
else
  log "SUCCESS" "gcloud account is correctly set to scoobyjava@cherry-ai.me"
fi

# Test GCP API access
log "INFO" "Testing GCP API access..."
if gcloud projects describe $PROJECT_ID &> /dev/null; then
  log "SUCCESS" "Successfully accessed GCP API"
else
  log "ERROR" "Failed to access GCP API. Please check your authentication."
  exit 1
fi

# Test Cloud Run service
log "INFO" "Testing Cloud Run service..."
if gcloud run services describe $SERVICE_NAME --region=$REGION &> /dev/null; then
  log "SUCCESS" "Cloud Run service $SERVICE_NAME exists"
  
  # Get the URL of the service
  SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
  log "INFO" "Cloud Run service URL: $SERVICE_URL"
  
  # Test the service
  log "INFO" "Testing the service..."
  if curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL | grep -q "200\|301\|302"; then
    log "SUCCESS" "Service is responding"
  else
    log "WARN" "Service is not responding. Please check the service logs."
  fi
else
  log "WARN" "Cloud Run service $SERVICE_NAME does not exist or you don't have permission to access it."
fi

# Test Cloud Storage buckets
log "INFO" "Testing Cloud Storage buckets..."
if gcloud storage ls gs://$PROJECT_ID-data &> /dev/null; then
  log "SUCCESS" "Cloud Storage bucket gs://$PROJECT_ID-data exists"
else
  log "WARN" "Cloud Storage bucket gs://$PROJECT_ID-data does not exist or you don't have permission to access it."
fi

# Test Firestore
log "INFO" "Testing Firestore..."
if gcloud firestore databases describe --project=$PROJECT_ID &> /dev/null; then
  log "SUCCESS" "Firestore database exists"
else
  log "WARN" "Firestore database does not exist or you don't have permission to access it."
fi

# Test Vertex AI
log "INFO" "Testing Vertex AI..."
if gcloud ai models list --region=$REGION --project=$PROJECT_ID &> /dev/null; then
  log "SUCCESS" "Vertex AI is accessible"
else
  log "WARN" "Vertex AI is not accessible or you don't have permission to access it."
fi

# Test Secret Manager
log "INFO" "Testing Secret Manager..."
if gcloud secrets list --project=$PROJECT_ID &> /dev/null; then
  log "SUCCESS" "Secret Manager is accessible"
else
  log "WARN" "Secret Manager is not accessible or you don't have permission to access it."
fi

# Test IAM permissions
log "INFO" "Testing IAM permissions..."
if gcloud projects get-iam-policy $PROJECT_ID &> /dev/null; then
  log "SUCCESS" "IAM permissions are accessible"
else
  log "WARN" "IAM permissions are not accessible or you don't have permission to access them."
fi

log "SUCCESS" "GCP deployment test completed!"
log "INFO" "Please review the output above to ensure all resources have been successfully provisioned and configured."