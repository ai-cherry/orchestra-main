#!/bin/bash
# check_gcloud.sh
# Script to check if gcloud is installed and provide instructions if not

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

# Check if gcloud is installed
if command -v gcloud &> /dev/null; then
  log "SUCCESS" "gcloud is installed!"
  log "INFO" "Checking gcloud configuration..."
  
  # Check if gcloud is configured with the correct project and account
  CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
  CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
  
  if [ "$CURRENT_PROJECT" = "cherry-ai-project" ]; then
    log "SUCCESS" "Project is correctly set to cherry-ai-project"
  else
    log "WARN" "Project is not set to cherry-ai-project. Current project: $CURRENT_PROJECT"
    log "INFO" "Setting project to cherry-ai-project..."
    gcloud config set project cherry-ai-project
  fi
  
  if [ "$CURRENT_ACCOUNT" = "scoobyjava@cherry-ai.me" ]; then
    log "SUCCESS" "Account is correctly set to scoobyjava@cherry-ai.me"
  else
    log "WARN" "Account is not set to scoobyjava@cherry-ai.me. Current account: $CURRENT_ACCOUNT"
    log "INFO" "Setting account to scoobyjava@cherry-ai.me..."
    gcloud config set account scoobyjava@cherry-ai.me
  fi
  
  # Verify environment variables
  log "INFO" "Verifying environment variables..."
  
  if [ -n "$CLOUDSDK_CORE_PROJECT" ] && [ "$CLOUDSDK_CORE_PROJECT" = "cherry-ai-project" ]; then
    log "SUCCESS" "CLOUDSDK_CORE_PROJECT is correctly set to cherry-ai-project"
  else
    log "WARN" "CLOUDSDK_CORE_PROJECT is not set correctly. Setting it now..."
    export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
  fi
  
  if [ -n "$CLOUDSDK_CORE_ACCOUNT" ] && [ "$CLOUDSDK_CORE_ACCOUNT" = "scoobyjava@cherry-ai.me" ]; then
    log "SUCCESS" "CLOUDSDK_CORE_ACCOUNT is correctly set to scoobyjava@cherry-ai.me"
  else
    log "WARN" "CLOUDSDK_CORE_ACCOUNT is not set correctly. Setting it now..."
    export CLOUDSDK_CORE_ACCOUNT="scoobyjava@cherry-ai.me"
  fi
  
  if [ -n "$CLOUDSDK_CORE_REGION" ] && [ "$CLOUDSDK_CORE_REGION" = "us-central1" ]; then
    log "SUCCESS" "CLOUDSDK_CORE_REGION is correctly set to us-central1"
  else
    log "WARN" "CLOUDSDK_CORE_REGION is not set correctly. Setting it now..."
    export CLOUDSDK_CORE_REGION="us-central1"
  fi
  
  if [ -n "$CLOUDSDK_CORE_ZONE" ] && [ "$CLOUDSDK_CORE_ZONE" = "us-central1-a" ]; then
    log "SUCCESS" "CLOUDSDK_CORE_ZONE is correctly set to us-central1-a"
  else
    log "WARN" "CLOUDSDK_CORE_ZONE is not set correctly. Setting it now..."
    export CLOUDSDK_CORE_ZONE="us-central1-a"
  fi
  
  log "SUCCESS" "GCP configuration is ready to use!"
else
  log "ERROR" "gcloud is not installed."
  log "INFO" "Setting environment variables for GCP configuration..."
  
  # Set environment variables
  export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
  export CLOUDSDK_CORE_ACCOUNT="scoobyjava@cherry-ai.me"
  export CLOUDSDK_CORE_REGION="us-central1"
  export CLOUDSDK_CORE_ZONE="us-central1-a"
  
  log "INFO" "Environment variables set:"
  log "INFO" "CLOUDSDK_CORE_PROJECT=cherry-ai-project"
  log "INFO" "CLOUDSDK_CORE_ACCOUNT=scoobyjava@cherry-ai.me"
  log "INFO" "CLOUDSDK_CORE_REGION=us-central1"
  log "INFO" "CLOUDSDK_CORE_ZONE=us-central1-a"
  
  log "INFO" "To install gcloud, follow these steps:"
  log "INFO" "1. Download the Google Cloud SDK:"
  log "INFO" "   curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-latest-linux-x86_64.tar.gz"
  log "INFO" "2. Extract the archive:"
  log "INFO" "   tar -xf google-cloud-cli-latest-linux-x86_64.tar.gz"
  log "INFO" "3. Run the install script:"
  log "INFO" "   ./google-cloud-sdk/install.sh --quiet"
  log "INFO" "4. Initialize gcloud:"
  log "INFO" "   ./google-cloud-sdk/bin/gcloud init"
  
  log "INFO" "After installation, run this script again to verify the configuration."
fi