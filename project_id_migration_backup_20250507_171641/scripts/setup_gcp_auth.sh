#!/bin/bash
# setup_gcp_auth.sh - Script to download GCP service account key from Secret Manager and authenticate gcloud CLI
# Project: orchestra-main

set -eo pipefail

# Configuration variables (adjust as needed or pass as arguments)
PROJECT_ID="agi-baby-cherry"
SECRET_NAME="agi-baby-cherry-gsa-key"
SERVICE_ACCOUNT="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
KEY_FILE_PATH="/workspaces/orchestra-main/credentials/agi-baby-cherry-gsa.json"

# Logging function to avoid exposing sensitive data
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Validate environment
validate_environment() {
  log "Validating environment..."
  if ! command -v gcloud &> /dev/null; then
    log "Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
  fi
  log "Environment validation passed."
}

# Create directory for key file if it doesn't exist
create_directory() {
  local dir_path=$(dirname "$KEY_FILE_PATH")
  if [[ ! -d "$dir_path" ]]; then
    log "Creating directory for key file..."
    mkdir -p "$dir_path"
    if [ $? -ne 0 ]; then
      log "Error: Failed to create directory for key file."
      exit 1
    fi
  fi
}

# Download service account key from GCP Secret Manager
download_key() {
  log "Downloading service account key from GCP Secret Manager..."
  gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" > "$KEY_FILE_PATH" 2>/dev/null
  if [ $? -ne 0 ]; then
    log "Error: Failed to download service account key. Check permissions or secret name."
    exit 1
  fi
  log "Service account key downloaded successfully."
}

# Set file permissions
set_permissions() {
  log "Setting permissions on key file..."
  chmod 600 "$KEY_FILE_PATH"
  if [ $? -ne 0 ]; then
    log "Error: Failed to set permissions on key file."
    exit 1
  fi
  log "Permissions set successfully."
}

# Set GOOGLE_APPLICATION_CREDENTIALS environment variable
set_credentials() {
  log "Setting GOOGLE_APPLICATION_CREDENTIALS environment variable..."
  export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE_PATH"
  echo "export GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE_PATH" >> ~/.bashrc
  source ~/.bashrc
  log "Environment variable set."
}

# Authenticate gcloud CLI
authenticate() {
  log "Authenticating gcloud CLI with service account..."
  gcloud auth activate-service-account "$SERVICE_ACCOUNT" --key-file="$KEY_FILE_PATH"
  if [ $? -ne 0 ]; then
    log "Error: Authentication failed. Check service account and key file."
    exit 1
  fi
  gcloud config set project "$PROJECT_ID"
  log "Authentication successful."
}

# Verify authentication
verify_auth() {
  log "Verifying GCP configuration..."
  gcloud config list
  if [ $? -ne 0 ]; then
    log "Error: Failed to list configuration."
    exit 1
  fi
  
  log "Verifying active accounts..."
  gcloud auth list
  if [ $? -ne 0 ]; then
    log "Error: Failed to list active accounts."
    exit 1
  fi
  log "Verification complete."
}

# Main execution flow
main() {
  log "Starting GCP authentication setup..."
  validate_environment
  create_directory
  download_key
  set_permissions
  set_credentials
  authenticate
  verify_auth
  log "GCP authentication setup completed successfully."
}

# Execute main function with any passed arguments
main "$@"