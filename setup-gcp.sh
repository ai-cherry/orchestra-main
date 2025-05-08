#!/bin/bash
# setup-gcp.sh - Comprehensive script to set up GCP environment in Codespaces
# This script handles authentication, API enabling, and verification
# Created for AI Orchestra project (cherry-ai-project)

# Exit on error
set -e

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
SERVICE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
REGION="us-central1"
ZONE="us-central1-a"

# Log function for consistent output
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

# Function to check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Function to check GCP authentication
check_gcp_auth() {
  log "INFO" "Checking GCP authentication..."
  
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI not found. Please install the Google Cloud SDK."
    return 1
  fi
  
  if gcloud auth list --quiet 2>/dev/null | grep -q "active"; then
    log "SUCCESS" "Already authenticated with GCP"
    return 0
  else
    log "INFO" "Not authenticated with GCP"
    return 1
  fi
}

# Function to authenticate with GCP
authenticate_gcp() {
  log "INFO" "Authenticating with GCP..."
  
  # Check if service account key file exists
  if [ ! -f "$HOME/.gcp/service-account.json" ]; then
    log "INFO" "Service account key file not found, creating it..."
    
    # Create directory for service account key
    mkdir -p $HOME/.gcp
    
    # Check if GCP_SERVICE_ACCOUNT_KEY is set (for backward compatibility)
    if [ -n "$GCP_SERVICE_ACCOUNT_KEY" ]; then
      log "INFO" "Using GCP_SERVICE_ACCOUNT_KEY environment variable"
      cp "$GCP_SERVICE_ACCOUNT_KEY" $HOME/.gcp/service-account.json
    # Check if GCP_MASTER_SERVICE_JSON is set (for backward compatibility)
    elif [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
      log "INFO" "Using GCP_MASTER_SERVICE_JSON environment variable"
      echo "$GCP_MASTER_SERVICE_JSON" > $HOME/.gcp/service-account.json
    else
      log "ERROR" "No service account key found"
      log "INFO" "Please set the GCP_SERVICE_ACCOUNT_KEY Codespaces secret"
      return 1
    fi
  else
    log "INFO" "Service account key file already exists"
  fi
  
  # Check if already authenticated with the service account
  if gcloud auth list --filter="account:$SERVICE_ACCOUNT" --format="value(account)" | grep -q "$SERVICE_ACCOUNT"; then
    log "INFO" "Already authenticated as $SERVICE_ACCOUNT"
  else
    # Activate service account
    log "INFO" "Activating service account..."
    gcloud auth activate-service-account $SERVICE_ACCOUNT --key-file=$HOME/.gcp/service-account.json
  fi
  
  # Set project
  gcloud config set project $PROJECT_ID
  
  # Set region and zone
  gcloud config set compute/region $REGION
  gcloud config set compute/zone $ZONE
  
  # Add environment variables to .bashrc if not already there
  if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS=\$HOME/.gcp/service-account.json" $HOME/.bashrc; then
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
    log "INFO" "Added GOOGLE_APPLICATION_CREDENTIALS to .bashrc"
  fi
  
  if ! grep -q "CLOUDSDK_CORE_DISABLE_PROMPTS=1" $HOME/.bashrc; then
    echo 'export CLOUDSDK_CORE_DISABLE_PROMPTS=1' >> $HOME/.bashrc
    log "INFO" "Added CLOUDSDK_CORE_DISABLE_PROMPTS to .bashrc"
  fi
  
  log "SUCCESS" "Successfully authenticated with GCP"
}

# Function to enable required APIs
enable_apis() {
  log "INFO" "Enabling required APIs..."
  
  # List of APIs to enable
  APIS=(
    "aiplatform.googleapis.com"      # Vertex AI
    "compute.googleapis.com"         # Compute Engine
    "storage.googleapis.com"         # Cloud Storage
    "workstations.googleapis.com"    # Cloud Workstations
    "notebooks.googleapis.com"       # Vertex AI Workbench
    "run.googleapis.com"             # Cloud Run
    "secretmanager.googleapis.com"   # Secret Manager
    "cloudbuild.googleapis.com"      # Cloud Build
  )
  
  for api in "${APIS[@]}"; do
    log "INFO" "Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
  done
  
  log "SUCCESS" "All required APIs enabled"
}

# Function to verify setup
verify_setup() {
  log "INFO" "Verifying setup..."
  
  # Check authentication
  log "INFO" "Checking authentication..."
  if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "$SERVICE_ACCOUNT"; then
    log "SUCCESS" "Authenticated as $SERVICE_ACCOUNT"
  else
    log "ERROR" "Not authenticated as $SERVICE_ACCOUNT"
    return 1
  fi
  
  # Check project
  log "INFO" "Checking project..."
  if [ "$(gcloud config get-value project)" = "$PROJECT_ID" ]; then
    log "SUCCESS" "Project set to $PROJECT_ID"
  else
    log "ERROR" "Project not set to $PROJECT_ID"
    return 1
  fi
  
  # Check APIs
  log "INFO" "Checking APIs..."
  for api in "aiplatform.googleapis.com" "compute.googleapis.com" "storage.googleapis.com"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
      log "SUCCESS" "$api is enabled"
    else
      log "ERROR" "$api is not enabled"
      return 1
    fi
  done
  
  log "SUCCESS" "Setup verification completed successfully"
}

# Main function
main() {
  log "INFO" "Starting GCP environment setup..."
  
  # Check if already authenticated
  if ! check_gcp_auth; then
    authenticate_gcp
  fi
  
  # Enable required APIs
  enable_apis
  
  # Verify setup
  verify_setup
  
  log "SUCCESS" "GCP environment setup completed successfully!"
  log "INFO" "You can now run the following commands to provision GCP IDEs:"
  log "INFO" "  ./setup-gcp-ides.sh"
  log "INFO" "Or to test your setup:"
  log "INFO" "  gcloud auth list && gcloud config get-value project"
}

# Run the main function
main