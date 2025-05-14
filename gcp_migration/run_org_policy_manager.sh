#!/bin/bash
#
# Run Organization Policy Manager for AI Orchestra GCP Migration
#
# This script executes the Organization Policy Manager with the
# necessary credentials from environment variables or interactive input.
#
# Author: Roo

set -e

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE_NAME="ai-orchestra-minimal"
TEMP_KEY_FILE="/tmp/org_policy_key_$$.json"
LOG_DIR="gcp_migration/migration_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/org_policy_manager_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  case $level in
    INFO)
      echo -e "${GREEN}[INFO]${NC} ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    ERROR)
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    STEP)
      echo -e "${BLUE}[STEP]${NC} ${BOLD}${message}${NC}"
      ;;
    *)
      echo -e "${message}"
      ;;
  esac
  
  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Function to cleanup temporary files on exit
cleanup() {
  log "INFO" "Cleaning up temporary files"
  # Remove temporary key file
  if [ -f "$TEMP_KEY_FILE" ]; then
    rm -f "$TEMP_KEY_FILE"
  fi
}

# Register cleanup function to run on script exit
trap cleanup EXIT

# Function to check if GitHub secrets are available
check_github_secrets() {
  log "STEP" "Checking for GitHub organization secrets"
  
  if [ -n "$GCP_ORGANIZATION_POLICY_JSON" ]; then
    log "INFO" "Found GCP_ORGANIZATION_POLICY_JSON environment variable"
    return 0
  fi
  
  log "WARNING" "GitHub secret GCP_ORGANIZATION_POLICY_JSON not found in environment"
  return 1
}

# Function to input credentials manually
input_credentials_manually() {
  log "STEP" "Manual credential input"
  
  log "INFO" "Please enter the path to the service account JSON key file:"
  read -p "Path: " KEY_FILE_PATH
  
  if [ -f "$KEY_FILE_PATH" ]; then
    export GCP_ORGANIZATION_POLICY_JSON=$(cat "$KEY_FILE_PATH")
    log "INFO" "Successfully loaded service account key from $KEY_FILE_PATH"
    return 0
  else
    log "ERROR" "File not found: $KEY_FILE_PATH"
    return 1
  fi
}

# Function to create a temporary key file
create_key_file() {
  log "STEP" "Creating temporary key file"
  
  echo "$GCP_ORGANIZATION_POLICY_JSON" > "$TEMP_KEY_FILE"
  log "INFO" "Temporary key file created at $TEMP_KEY_FILE"
}

# Function to run the organization policy manager
run_org_policy_manager() {
  log "STEP" "Running Organization Policy Manager"
  
  log "INFO" "Executing Organization Policy Manager script"
  
  if [ -f "$TEMP_KEY_FILE" ]; then
    log "INFO" "Using temporary key file"
    python3 gcp_migration/use_org_policy_manager.py \
      --json-secret="$TEMP_KEY_FILE" \
      --project-id="$PROJECT_ID" \
      --service-name="$SERVICE_NAME" \
      --region="$REGION" 2>&1 | tee -a "$LOG_FILE"
  else
    log "INFO" "Using environment variable"
    python3 gcp_migration/use_org_policy_manager.py \
      --project-id="$PROJECT_ID" \
      --service-name="$SERVICE_NAME" \
      --region="$REGION" 2>&1 | tee -a "$LOG_FILE"
  fi
  
  local exit_code=${PIPESTATUS[0]}
  if [ $exit_code -ne 0 ]; then
    log "ERROR" "Organization Policy Manager failed with exit code $exit_code"
    return $exit_code
  fi
  
  log "INFO" "Organization Policy Manager completed successfully"
  return 0
}

# Function to verify the changes
verify_changes() {
  log "STEP" "Verifying organization policy changes"
  
  # Get service URL
  log "INFO" "Getting Cloud Run service URL"
  local SERVICE_URL
  SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
  
  if [ -n "$SERVICE_URL" ]; then
    log "INFO" "Testing service URL: $SERVICE_URL"
    curl -s -i "${SERVICE_URL}/health" 2>&1 | tee -a "$LOG_FILE"
  else
    log "WARNING" "Could not get service URL"
  fi
  
  # Test Vertex AI
  log "INFO" "Testing Vertex AI connectivity"
  python3 gcp_migration/test_vertex_ai.py 2>&1 | tee -a "$LOG_FILE"
  
  # Check organization policies
  log "INFO" "Checking updated organization policies"
  gcloud org-policies list --project="$PROJECT_ID" 2>&1 | tee -a "$LOG_FILE"
}

# Function to run the migration script after fixing policies
run_migration_script() {
  log "STEP" "Running migration script"
  
  log "INFO" "Executing fixed migration script"
  ./gcp_migration/execute_non_interactive.sh 2>&1 | tee -a "$LOG_FILE"
  
  local exit_code=${PIPESTATUS[0]}
  if [ $exit_code -ne 0 ]; then
    log "WARNING" "Migration script completed with exit code $exit_code"
  else
    log "INFO" "Migration script completed successfully"
  fi
}

# Main function
main() {
  log "INFO" "Starting organization policy fix for AI Orchestra GCP migration"
  
  # Check for GitHub secrets
  if ! check_github_secrets; then
    if ! input_credentials_manually; then
      log "ERROR" "Failed to get service account credentials"
      exit 1
    fi
  fi
  
  # Create temporary key file
  create_key_file
  
  # Run the organization policy manager
  if ! run_org_policy_manager; then
    log "ERROR" "Failed to update organization policies"
    exit 1
  fi
  
  # Verify the changes
  verify_changes
  
  # Run the migration script
  log "INFO" "Do you want to run the migration script now? (y/n)"
  read -p "Run migration script? " RUN_MIGRATION
  
  if [[ "$RUN_MIGRATION" =~ ^[Yy] ]]; then
    run_migration_script
    log "INFO" "Migration process completed. Check the log for details: $LOG_FILE"
  else
    log "INFO" "Skipping migration script"
    log "INFO" "To run it later, use: ./gcp_migration/execute_non_interactive.sh"
  fi
  
  log "STEP" "Organization policy fix completed"
  echo -e "\n${GREEN}${BOLD}Organization policy fix completed!${NC}"
  echo -e "Detailed logs available at: ${LOG_FILE}"
}

# Execute main function
main "$@"