#!/bin/bash
# ensure_gcp_env.sh
# Script to ensure GCP environment variables are set correctly

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

# Check and set environment variables
log "INFO" "Checking GCP environment variables..."

# Check CLOUDSDK_CORE_PROJECT
if [ -z "$CLOUDSDK_CORE_PROJECT" ] || [ "$CLOUDSDK_CORE_PROJECT" != "cherry-ai-project" ]; then
  log "WARN" "CLOUDSDK_CORE_PROJECT is not set correctly. Setting it now..."
  export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
else
  log "SUCCESS" "CLOUDSDK_CORE_PROJECT is correctly set to cherry-ai-project"
fi

# Check CLOUDSDK_CORE_ACCOUNT
if [ -z "$CLOUDSDK_CORE_ACCOUNT" ] || [ "$CLOUDSDK_CORE_ACCOUNT" != "scoobyjava@cherry-ai.me" ]; then
  log "WARN" "CLOUDSDK_CORE_ACCOUNT is not set correctly. Setting it now..."
  export CLOUDSDK_CORE_ACCOUNT="scoobyjava@cherry-ai.me"
else
  log "SUCCESS" "CLOUDSDK_CORE_ACCOUNT is correctly set to scoobyjava@cherry-ai.me"
fi

# Check CLOUDSDK_CORE_REGION
if [ -z "$CLOUDSDK_CORE_REGION" ] || [ "$CLOUDSDK_CORE_REGION" != "us-central1" ]; then
  log "WARN" "CLOUDSDK_CORE_REGION is not set correctly. Setting it now..."
  export CLOUDSDK_CORE_REGION="us-central1"
else
  log "SUCCESS" "CLOUDSDK_CORE_REGION is correctly set to us-central1"
fi

# Check CLOUDSDK_CORE_ZONE
if [ -z "$CLOUDSDK_CORE_ZONE" ] || [ "$CLOUDSDK_CORE_ZONE" != "us-central1-a" ]; then
  log "WARN" "CLOUDSDK_CORE_ZONE is not set correctly. Setting it now..."
  export CLOUDSDK_CORE_ZONE="us-central1-a"
else
  log "SUCCESS" "CLOUDSDK_CORE_ZONE is correctly set to us-central1-a"
fi

# Verify environment variables
log "INFO" "Verifying environment variables..."
log "INFO" "CLOUDSDK_CORE_PROJECT=$CLOUDSDK_CORE_PROJECT"
log "INFO" "CLOUDSDK_CORE_ACCOUNT=$CLOUDSDK_CORE_ACCOUNT"
log "INFO" "CLOUDSDK_CORE_REGION=$CLOUDSDK_CORE_REGION"
log "INFO" "CLOUDSDK_CORE_ZONE=$CLOUDSDK_CORE_ZONE"

log "SUCCESS" "GCP environment variables are set correctly!"