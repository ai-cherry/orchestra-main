#!/bin/bash
# setup-env.sh - Centralized environment configuration for AI Orchestra

# Text formatting
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Auto-repair function
auto_repair() {
  local issue=$1
  local fixed=false

  case $issue in
    "service_account")
      echo -e "${YELLOW}Attempting to repair missing service account file...${NC}"
      if [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
        mkdir -p $HOME/.gcp
        echo "$GCP_MASTER_SERVICE_JSON" > $HOME/.gcp/service-account.json
        if [[ -f "$HOME/.gcp/service-account.json" ]]; then
          echo -e "${GREEN}Successfully created service account file${NC}"
          fixed=true
        else
          echo -e "${RED}Failed to create service account file${NC}"
        fi
      else
        echo -e "${RED}GCP_MASTER_SERVICE_JSON environment variable not set${NC}"
        echo "Please set the GCP_MASTER_SERVICE_JSON environment variable or manually create the service account file"
      fi
      ;;
    "gcloud_path")
      echo -e "${YELLOW}Attempting to repair gcloud path...${NC}"
      for gcloud_path in \
        "/workspaces/orchestra-main/google-cloud-sdk/bin" \
        "$HOME/google-cloud-sdk/bin" \
        "/usr/local/google-cloud-sdk/bin" \
        "/usr/share/google-cloud-sdk/bin"; do
        
        if [[ -d "$gcloud_path" ]]; then
          echo -e "${GREEN}Found gcloud at $gcloud_path, adding to PATH${NC}"
          export PATH=$PATH:$gcloud_path
          fixed=true
          break
        fi
      done
      
      if [[ "$fixed" != "true" ]]; then
        echo -e "${RED}Could not find gcloud installation${NC}"
      fi
      ;;
  esac

  return $fixed
}

# Check for critical files
if [[ ! -f "$HOME/.gcp/service-account.json" ]]; then
  echo -e "${YELLOW}WARNING: Service account file not found at $HOME/.gcp/service-account.json${NC}"
  auto_repair "service_account"
fi

# Check for gcloud in PATH
if ! command -v gcloud &> /dev/null; then
  echo -e "${YELLOW}WARNING: gcloud not found in PATH${NC}"
  auto_repair "gcloud_path"
fi

# GCP Configuration
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
export CLOUDSDK_CORE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
export CLOUDSDK_CORE_REGION="us-central1"
export CLOUDSDK_CORE_ZONE="us-central1-a"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Standard Mode Configuration
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true

# AI Orchestra Specific Configuration
export ORCHESTRA_ENV="development"
export ORCHESTRA_LOG_LEVEL="info"

# Path Configuration
export PATH=$PATH:$HOME/google-cloud-sdk/bin:/workspaces/orchestra-main/google-cloud-sdk/bin

# VSCode IDE Integration
export CLOUDCODE_ENABLE=true
export CLOUDCODE_PROJECT="cherry-ai-project"
export CLOUDCODE_REGION="us-central1"

# Print configuration status
echo -e "${GREEN}AI Orchestra environment configured successfully${NC}"
echo "GCP Project: $CLOUDSDK_CORE_PROJECT"
echo "GCP Region: $CLOUDSDK_CORE_REGION"
echo "Standard Mode: $STANDARD_MODE"