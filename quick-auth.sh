#!/bin/bash
# quick-auth.sh - Quickly re-authenticate with GCP without rebuilding Codespace

# Log file for debugging
LOG_FILE="$HOME/quick-auth.log"

# Initialize log file
echo "===== $(date) =====" > "$LOG_FILE"
echo "Starting GCP quick authentication" >> "$LOG_FILE"

# Text formatting
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
  local level=$1
  local message=$2
  local color=$NC
  
  case $level in
    "INFO")
      color=$BLUE
      ;;
    "WARNING")
      color=$YELLOW
      ;;
    "ERROR")
      color=$RED
      ;;
    "SUCCESS")
      color=$GREEN
      ;;
  esac
  
  echo -e "${color}[$level] $message${NC}" | tee -a "$LOG_FILE"
}

echo "======================================================"
echo "  AI ORCHESTRA GCP QUICK AUTHENTICATION"
echo "======================================================"
log_message "INFO" "Starting GCP quick authentication process"

# Check if service account file exists
if [[ ! -f "$HOME/.gcp/service-account.json" ]]; then
  log_message "ERROR" "Service account file not found at $HOME/.gcp/service-account.json"
  
  # Try to recover by checking if GCP_MASTER_SERVICE_JSON is set
  if [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
    log_message "WARNING" "Attempting to recover by creating service account file from environment variable"
    mkdir -p $HOME/.gcp
    echo "$GCP_MASTER_SERVICE_JSON" > $HOME/.gcp/service-account.json 2>> "$LOG_FILE"
    
    if [[ -f "$HOME/.gcp/service-account.json" ]]; then
      log_message "SUCCESS" "Successfully created service account file"
    else
      log_message "ERROR" "Failed to create service account file"
      echo "Check $LOG_FILE for more details"
      exit 1
    fi
  else
    log_message "ERROR" "GCP_MASTER_SERVICE_JSON environment variable not set"
    echo "Please set the GCP_MASTER_SERVICE_JSON environment variable or manually create the service account file"
    exit 1
  fi
fi

# Authenticate with GCP
log_message "INFO" "Authenticating with GCP"
gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json >> "$LOG_FILE" 2>&1

# Check if authentication was successful
if [[ $? -eq 0 ]]; then
  log_message "SUCCESS" "Successfully authenticated with GCP"
else
  log_message "ERROR" "Failed to authenticate with GCP"
  echo "Check $LOG_FILE for more details"
  exit 1
fi

# Set project
log_message "INFO" "Setting GCP project"
gcloud config set project cherry-ai-project >> "$LOG_FILE" 2>&1

# Set region and zone
log_message "INFO" "Setting GCP region and zone"
gcloud config set compute/region us-central1 >> "$LOG_FILE" 2>&1
gcloud config set compute/zone us-central1-a >> "$LOG_FILE" 2>&1

# Set environment variables
log_message "INFO" "Setting environment variables"
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
export CLOUDSDK_CORE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
export CLOUDSDK_CORE_REGION="us-central1"
export CLOUDSDK_CORE_ZONE="us-central1-a"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Log environment variables (without sensitive data)
echo "Environment variables set:" >> "$LOG_FILE"
echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS" >> "$LOG_FILE"
echo "CLOUDSDK_CORE_PROJECT=$CLOUDSDK_CORE_PROJECT" >> "$LOG_FILE"
echo "CLOUDSDK_CORE_REGION=$CLOUDSDK_CORE_REGION" >> "$LOG_FILE"
echo "CLOUDSDK_CORE_ZONE=$CLOUDSDK_CORE_ZONE" >> "$LOG_FILE"

# Source the centralized environment configuration
if [[ -f "$HOME/setup-env.sh" ]]; then
  log_message "INFO" "Sourcing centralized environment configuration"
  source ~/setup-env.sh
  echo "Sourced setup-env.sh" >> "$LOG_FILE"
else
  log_message "WARNING" "Centralized environment configuration not found at $HOME/setup-env.sh"
  log_message "WARNING" "Using basic environment configuration"
fi

# Test GCP connectivity
log_message "INFO" "Testing GCP connectivity"
if gcloud projects describe cherry-ai-project --format="value(name)" >> "$LOG_FILE" 2>&1; then
  log_message "SUCCESS" "Successfully connected to GCP project: cherry-ai-project"
else
  log_message "ERROR" "Failed to connect to GCP project"
  echo "Check $LOG_FILE for more details"
  exit 1
fi

echo "======================================================"
log_message "SUCCESS" "GCP AUTHENTICATION COMPLETE"
echo "======================================================"
echo "You are now authenticated with GCP and ready to use GCP services"
echo "Active account: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
echo "Current project: $(gcloud config get-value project)"
echo "Current region: $(gcloud config get-value compute/region)"
echo "Current zone: $(gcloud config get-value compute/zone)"
echo "======================================================"
echo "Log file: $LOG_FILE"