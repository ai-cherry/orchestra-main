#!/bin/bash
# test-rebuild.sh - Test the Codespace rebuild process

# Text formatting
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="$HOME/rebuild-test.log"
echo "===== $(date) =====" > "$LOG_FILE"
echo "Starting rebuild test" >> "$LOG_FILE"

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
echo "  TESTING CODESPACE REBUILD PROCESS"
echo "======================================================"
log_message "INFO" "This script simulates a Codespace rebuild to test the authentication persistence"

# Step 1: Check current authentication status
log_message "INFO" "Checking current GCP authentication status"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  log_message "SUCCESS" "Currently authenticated as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
else
  log_message "WARNING" "Not currently authenticated with GCP"
  log_message "INFO" "Will attempt to authenticate during simulated rebuild"
fi

# Step 2: Check for setup_and_verify.sh script
log_message "INFO" "Checking for setup_and_verify.sh script"
if [[ -f "/workspaces/orchestra-main/.devcontainer/setup_and_verify.sh" ]]; then
  log_message "SUCCESS" "Found setup_and_verify.sh script"
else
  log_message "ERROR" "setup_and_verify.sh script not found at /workspaces/orchestra-main/.devcontainer/setup_and_verify.sh"
  log_message "INFO" "Please ensure the script exists and is executable"
  exit 1
fi

# Step 3: Make sure the script is executable
log_message "INFO" "Making sure setup_and_verify.sh is executable"
chmod +x /workspaces/orchestra-main/.devcontainer/setup_and_verify.sh

# Step 4: Simulate a rebuild by running the setup_and_verify.sh script with the --rebuild flag
log_message "INFO" "Simulating rebuild by running setup_and_verify.sh with --rebuild flag"
/workspaces/orchestra-main/.devcontainer/setup_and_verify.sh --rebuild

# Step 5: Check if the rebuild was successful
log_message "INFO" "Checking if rebuild was successful"
if [[ -f "/workspaces/orchestra-main/codespace_rebuild.log" ]]; then
  log_message "SUCCESS" "Rebuild log file created"
else
  log_message "ERROR" "Rebuild log file not created"
  exit 1
fi

# Step 6: Verify GCP authentication after rebuild
log_message "INFO" "Verifying GCP authentication after rebuild"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  log_message "SUCCESS" "Successfully authenticated after rebuild as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
else
  log_message "ERROR" "Not authenticated with GCP after rebuild"
  exit 1
fi

# Step 7: Test GCP API access
log_message "INFO" "Testing GCP API access"
if gcloud projects describe cherry-ai-project --format="value(name)" &>/dev/null; then
  log_message "SUCCESS" "Successfully accessed GCP project information"
else
  log_message "ERROR" "Failed to access GCP project information"
  exit 1
fi

# Step 8: Check environment variables
log_message "INFO" "Checking environment variables"
if [[ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
  log_message "SUCCESS" "GOOGLE_APPLICATION_CREDENTIALS is set to: $GOOGLE_APPLICATION_CREDENTIALS"
else
  log_message "ERROR" "GOOGLE_APPLICATION_CREDENTIALS is not set"
  exit 1
fi

echo "======================================================"
log_message "SUCCESS" "REBUILD TEST COMPLETE"
echo "======================================================"
echo "The rebuild process was successfully tested"
echo "GCP authentication is working correctly after rebuild"
echo "Log file: $LOG_FILE"
echo "======================================================"