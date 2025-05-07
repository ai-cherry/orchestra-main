#!/bin/bash
# verify_gcp_config.sh
# Script to verify the GCP configuration and provide instructions on how to fix any issues

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

# Check if the scripts exist
log "INFO" "Checking if the required scripts exist..."
MISSING_SCRIPTS=0

if [ ! -f hardcode_gcp_config.sh ]; then
  log "ERROR" "hardcode_gcp_config.sh not found"
  MISSING_SCRIPTS=1
else
  log "SUCCESS" "hardcode_gcp_config.sh found"
fi

if [ ! -f check_gcloud.sh ]; then
  log "ERROR" "check_gcloud.sh not found"
  MISSING_SCRIPTS=1
else
  log "SUCCESS" "check_gcloud.sh found"
fi

if [ ! -f ensure_gcp_env.sh ]; then
  log "ERROR" "ensure_gcp_env.sh not found"
  MISSING_SCRIPTS=1
else
  log "SUCCESS" "ensure_gcp_env.sh found"
fi

if [ ! -f source_env_and_ensure_gcp.sh ]; then
  log "ERROR" "source_env_and_ensure_gcp.sh not found"
  MISSING_SCRIPTS=1
else
  log "SUCCESS" "source_env_and_ensure_gcp.sh found"
fi

if [ ! -f add_to_bashrc.sh ]; then
  log "ERROR" "add_to_bashrc.sh not found"
  MISSING_SCRIPTS=1
else
  log "SUCCESS" "add_to_bashrc.sh found"
fi

if [ $MISSING_SCRIPTS -eq 1 ]; then
  log "ERROR" "Some scripts are missing. Please run the setup again."
  exit 1
fi

# Check if the scripts are executable
log "INFO" "Checking if the scripts are executable..."
NOT_EXECUTABLE=0

if [ ! -x hardcode_gcp_config.sh ]; then
  log "WARN" "hardcode_gcp_config.sh is not executable. Making it executable..."
  chmod +x hardcode_gcp_config.sh
else
  log "SUCCESS" "hardcode_gcp_config.sh is executable"
fi

if [ ! -x check_gcloud.sh ]; then
  log "WARN" "check_gcloud.sh is not executable. Making it executable..."
  chmod +x check_gcloud.sh
else
  log "SUCCESS" "check_gcloud.sh is executable"
fi

if [ ! -x ensure_gcp_env.sh ]; then
  log "WARN" "ensure_gcp_env.sh is not executable. Making it executable..."
  chmod +x ensure_gcp_env.sh
else
  log "SUCCESS" "ensure_gcp_env.sh is executable"
fi

if [ ! -x source_env_and_ensure_gcp.sh ]; then
  log "WARN" "source_env_and_ensure_gcp.sh is not executable. Making it executable..."
  chmod +x source_env_and_ensure_gcp.sh
else
  log "SUCCESS" "source_env_and_ensure_gcp.sh is executable"
fi

if [ ! -x add_to_bashrc.sh ]; then
  log "WARN" "add_to_bashrc.sh is not executable. Making it executable..."
  chmod +x add_to_bashrc.sh
else
  log "SUCCESS" "add_to_bashrc.sh is executable"
fi

# Check if the .env file exists
log "INFO" "Checking if the .env file exists..."
if [ ! -f .env ]; then
  log "WARN" ".env file not found. Creating it..."
  ./source_env_and_ensure_gcp.sh
else
  log "SUCCESS" ".env file found"
fi

# Check if the environment variables are set
log "INFO" "Checking if the environment variables are set..."
ENV_VARS_SET=1

if [ -z "$CLOUDSDK_CORE_PROJECT" ] || [ "$CLOUDSDK_CORE_PROJECT" != "cherry-ai-project" ]; then
  log "WARN" "CLOUDSDK_CORE_PROJECT is not set correctly"
  ENV_VARS_SET=0
else
  log "SUCCESS" "CLOUDSDK_CORE_PROJECT is correctly set to cherry-ai-project"
fi

if [ -z "$CLOUDSDK_CORE_ACCOUNT" ] || [ "$CLOUDSDK_CORE_ACCOUNT" != "scoobyjava@cherry-ai.me" ]; then
  log "WARN" "CLOUDSDK_CORE_ACCOUNT is not set correctly"
  ENV_VARS_SET=0
else
  log "SUCCESS" "CLOUDSDK_CORE_ACCOUNT is correctly set to scoobyjava@cherry-ai.me"
fi

if [ -z "$CLOUDSDK_CORE_REGION" ] || [ "$CLOUDSDK_CORE_REGION" != "us-central1" ]; then
  log "WARN" "CLOUDSDK_CORE_REGION is not set correctly"
  ENV_VARS_SET=0
else
  log "SUCCESS" "CLOUDSDK_CORE_REGION is correctly set to us-central1"
fi

if [ -z "$CLOUDSDK_CORE_ZONE" ] || [ "$CLOUDSDK_CORE_ZONE" != "us-central1-a" ]; then
  log "WARN" "CLOUDSDK_CORE_ZONE is not set correctly"
  ENV_VARS_SET=0
else
  log "SUCCESS" "CLOUDSDK_CORE_ZONE is correctly set to us-central1-a"
fi

if [ $ENV_VARS_SET -eq 0 ]; then
  log "WARN" "Some environment variables are not set correctly. Running ensure_gcp_env.sh..."
  ./ensure_gcp_env.sh
else
  log "SUCCESS" "All environment variables are set correctly"
fi

# Check if source_env_and_ensure_gcp.sh is in .bashrc
log "INFO" "Checking if source_env_and_ensure_gcp.sh is in .bashrc..."
if ! grep -q "source_env_and_ensure_gcp.sh" ~/.bashrc; then
  log "WARN" "source_env_and_ensure_gcp.sh is not in .bashrc. Running add_to_bashrc.sh..."
  ./add_to_bashrc.sh
else
  log "SUCCESS" "source_env_and_ensure_gcp.sh is in .bashrc"
fi

# Check if gcloud is installed
log "INFO" "Checking if gcloud is installed..."
if ! command -v gcloud &> /dev/null; then
  log "WARN" "gcloud is not installed. Running check_gcloud.sh..."
  ./check_gcloud.sh
else
  log "SUCCESS" "gcloud is installed"
  
  # Check if gcloud is configured correctly
  log "INFO" "Checking if gcloud is configured correctly..."
  CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
  CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
  
  if [ "$CURRENT_PROJECT" != "cherry-ai-project" ]; then
    log "WARN" "gcloud project is not set correctly. Current project: $CURRENT_PROJECT"
    log "INFO" "Setting project to cherry-ai-project..."
    gcloud config set project cherry-ai-project
  else
    log "SUCCESS" "gcloud project is correctly set to cherry-ai-project"
  fi
  
  if [ "$CURRENT_ACCOUNT" != "scoobyjava@cherry-ai.me" ]; then
    log "WARN" "gcloud account is not set correctly. Current account: $CURRENT_ACCOUNT"
    log "INFO" "Setting account to scoobyjava@cherry-ai.me..."
    gcloud config set account scoobyjava@cherry-ai.me
  else
    log "SUCCESS" "gcloud account is correctly set to scoobyjava@cherry-ai.me"
  fi
fi

log "SUCCESS" "GCP configuration verification complete!"
log "INFO" "You can now use GCP commands with the following configuration:"
log "INFO" "Project: $CLOUDSDK_CORE_PROJECT"
log "INFO" "Account: $CLOUDSDK_CORE_ACCOUNT"
log "INFO" "Region: $CLOUDSDK_CORE_REGION"
log "INFO" "Zone: $CLOUDSDK_CORE_ZONE"