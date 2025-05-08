#!/bin/bash
# setup_service_account.sh - Easy setup for GCP service account authentication
# This script helps users set up non-interactive authentication for GCP

set -e

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log file for debugging
LOG_FILE="$HOME/setup_service_account.log"

# Initialize log file
echo "===== $(date) =====" > "$LOG_FILE"
echo "Starting service account setup" >> "$LOG_FILE"

# Function to display messages
log() {
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
    "STEP")
      color=$BOLD
      ;;
  esac
  
  echo -e "${color}[$level] $message${NC}" | tee -a "$LOG_FILE"
}

echo "======================================================"
echo "  AI ORCHESTRA GCP SERVICE ACCOUNT SETUP"
echo "======================================================"

# Check if we already have a service account key
if [[ -f "$HOME/.gcp/service-account.json" ]]; then
  log "INFO" "Service account key file already exists at $HOME/.gcp/service-account.json"
  
  # Verify the key file is valid JSON
  if jq . "$HOME/.gcp/service-account.json" > /dev/null 2>&1; then
    log "SUCCESS" "Service account key appears to be valid JSON"
  else
    log "ERROR" "Service account key file exists but is not valid JSON"
    log "INFO" "You may need to recreate your service account key"
  fi
  
  # Set environment variables
  export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcp/service-account.json"
  log "INFO" "Set GOOGLE_APPLICATION_CREDENTIALS environment variable"
  
  # Add to .bashrc if not already there
  if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json" $HOME/.bashrc; then
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
    log "SUCCESS" "Added GOOGLE_APPLICATION_CREDENTIALS to .bashrc"
  fi
  
  # Test authentication
  log "STEP" "Testing GCP authentication..."
  if gcloud auth activate-service-account --key-file="$HOME/.gcp/service-account.json" >> "$LOG_FILE" 2>&1; then
    log "SUCCESS" "Successfully authenticated with GCP"
    
    # Get the authenticated account
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log "INFO" "Authenticated as: $ACCOUNT"
    
    # Set project
    gcloud config set project cherry-ai-project >> "$LOG_FILE" 2>&1
    log "INFO" "Set project to: $(gcloud config get-value project)"
  else
    log "ERROR" "Failed to authenticate with GCP using the service account key"
    log "INFO" "Check the log file at $LOG_FILE for details"
  fi
  
  echo ""
  log "SUCCESS" "Your service account key is set up and ready to use"
  log "INFO" "All deployment scripts will now use this key for non-interactive authentication"
  echo "======================================================"
  exit 0
fi

# Create directory for service account key
log "STEP" "Setting up service account key directory..."
mkdir -p "$HOME/.gcp"

# Explain the process
log "INFO" "You need a GCP service account key for non-interactive authentication"
log "INFO" "This allows deployment scripts to run without browser prompts"
echo ""
log "STEP" "How to set up a service account key:"
echo ""
echo "Option 1: Use an existing service account key"
echo "----------------------------------------"
echo "1. If you have an existing service account key, copy it to:"
echo "   $HOME/.gcp/service-account.json"
echo ""
echo "Option 2: Create a new service account key"
echo "----------------------------------------"
echo "1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts"
echo "2. Select your project: cherry-ai-project"
echo "3. Click 'CREATE SERVICE ACCOUNT'"
echo "4. Name: 'deployment-account'"
echo "5. Description: 'Non-interactive deployment service account'"
echo "6. Click 'CREATE AND CONTINUE'"
echo "7. Add these roles:"
echo "   - Cloud Run Admin (roles/run.admin)"
echo "   - Artifact Registry Administrator (roles/artifactregistry.admin)"
echo "   - Service Account User (roles/iam.serviceAccountUser)"
echo "8. Click 'CONTINUE' and then 'DONE'"
echo "9. Find your new service account in the list and click on it"
echo "10. Go to the 'KEYS' tab"
echo "11. Click 'ADD KEY' → 'Create new key'"
echo "12. Choose 'JSON' format and click 'CREATE'"
echo "13. Save the downloaded key to: $HOME/.gcp/service-account.json"
echo ""
echo "Option 3: Set up via environment variable"
echo "----------------------------------------"
echo "1. Export your service account JSON as an environment variable:"
echo "   export GCP_MASTER_SERVICE_JSON='{ \"type\": \"service_account\", ... }'"
echo ""

# Prompt user
read -p "Have you placed a service account key at $HOME/.gcp/service-account.json? (y/n): " response

if [[ "$response" =~ ^[Yy]$ ]]; then
  # Check if the file exists
  if [[ -f "$HOME/.gcp/service-account.json" ]]; then
    log "INFO" "Service account key file found, setting up authentication..."
    
    # Set environment variables
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcp/service-account.json"
    log "INFO" "Set GOOGLE_APPLICATION_CREDENTIALS environment variable"
    
    # Add to .bashrc
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
    log "INFO" "Added GOOGLE_APPLICATION_CREDENTIALS to .bashrc"
    
    # Test authentication
    log "STEP" "Testing GCP authentication..."
    if gcloud auth activate-service-account --key-file="$HOME/.gcp/service-account.json" >> "$LOG_FILE" 2>&1; then
      log "SUCCESS" "Successfully authenticated with GCP"
      
      # Get the authenticated account
      ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
      log "INFO" "Authenticated as: $ACCOUNT"
      
      # Set project
      gcloud config set project cherry-ai-project >> "$LOG_FILE" 2>&1
      log "INFO" "Set project to: $(gcloud config get-value project)"
      
      echo ""
      log "SUCCESS" "Setup complete! You can now use deploy.sh without browser-based authentication"
    else
      log "ERROR" "Failed to authenticate with GCP using the service account key"
      log "INFO" "Check the log file at $LOG_FILE for details"
    fi
  else
    log "ERROR" "Service account key file not found at $HOME/.gcp/service-account.json"
    log "INFO" "Please follow the instructions above to set up your service account key"
  fi
else
  log "INFO" "Please set up your service account key and run this script again"
  log "INFO" "You can use deployment scripts without it, but may need to authenticate via browser"
fi

echo "======================================================"
echo ""
log "INFO" "For more information about GCP authentication, see:"
log "INFO" "https://cloud.google.com/sdk/docs/authorizing"
echo ""
