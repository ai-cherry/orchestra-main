#!/bin/bash
# set_gcloud_config.sh
# Script to set up gcloud configuration for the AI Orchestra project

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
ACCOUNT="scoobyjava@cherry-ai.me"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  log "ERROR" "gcloud is required but not installed. Please install it and try again."
  log "INFO" "You can install gcloud by following the instructions at: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Set environment variables
log "INFO" "Setting environment variables..."
echo "export CLOUDSDK_CORE_PROJECT=\"${PROJECT_ID}\"" >> ~/.bashrc
echo "export CLOUDSDK_CORE_ACCOUNT=\"${ACCOUNT}\"" >> ~/.bashrc

# Apply changes to current session
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
export CLOUDSDK_CORE_ACCOUNT="${ACCOUNT}"

# Set gcloud configuration
log "INFO" "Setting gcloud configuration..."
gcloud config set project ${PROJECT_ID}
gcloud config set account ${ACCOUNT}

# Verify configuration
log "INFO" "Verifying gcloud configuration..."
gcloud config list

log "SUCCESS" "gcloud configuration set up successfully!"
log "INFO" "Project ID: ${PROJECT_ID}"
log "INFO" "Account: ${ACCOUNT}"
log "INFO" "You can now use gcloud commands with this configuration."
log "INFO" "To apply the changes to a new terminal session, run: source ~/.bashrc"