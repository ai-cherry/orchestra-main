#!/bin/bash
# setup_and_verify_gcp.sh
# Script to set up and verify the GCP configuration

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
fi

if [ ! -f check_gcloud.sh ]; then
  log "ERROR" "check_gcloud.sh not found"
  MISSING_SCRIPTS=1
fi

if [ ! -f ensure_gcp_env.sh ]; then
  log "ERROR" "ensure_gcp_env.sh not found"
  MISSING_SCRIPTS=1
fi

if [ ! -f source_env_and_ensure_gcp.sh ]; then
  log "ERROR" "source_env_and_ensure_gcp.sh not found"
  MISSING_SCRIPTS=1
fi

if [ ! -f add_to_bashrc.sh ]; then
  log "ERROR" "add_to_bashrc.sh not found"
  MISSING_SCRIPTS=1
fi

if [ ! -f verify_gcp_config.sh ]; then
  log "ERROR" "verify_gcp_config.sh not found"
  MISSING_SCRIPTS=1
fi

if [ ! -f test_gcp_deployment.sh ]; then
  log "ERROR" "test_gcp_deployment.sh not found"
  MISSING_SCRIPTS=1
fi

if [ $MISSING_SCRIPTS -eq 1 ]; then
  log "ERROR" "Some scripts are missing. Please ensure all required scripts are present."
  exit 1
fi

# Make sure all scripts are executable
log "INFO" "Making all scripts executable..."
chmod +x hardcode_gcp_config.sh
chmod +x check_gcloud.sh
chmod +x ensure_gcp_env.sh
chmod +x source_env_and_ensure_gcp.sh
chmod +x add_to_bashrc.sh
chmod +x verify_gcp_config.sh
chmod +x test_gcp_deployment.sh

# Run the scripts in the correct order
log "INFO" "Running hardcode_gcp_config.sh..."
./hardcode_gcp_config.sh

log "INFO" "Running check_gcloud.sh..."
./check_gcloud.sh

log "INFO" "Running ensure_gcp_env.sh..."
./ensure_gcp_env.sh

log "INFO" "Running source_env_and_ensure_gcp.sh..."
source ./source_env_and_ensure_gcp.sh

log "INFO" "Running add_to_bashrc.sh..."
./add_to_bashrc.sh

log "INFO" "Running verify_gcp_config.sh..."
./verify_gcp_config.sh

# Check if gcloud is installed
if command -v gcloud &> /dev/null; then
  log "INFO" "Running test_gcp_deployment.sh..."
  ./test_gcp_deployment.sh
else
  log "WARN" "gcloud is not installed. Skipping test_gcp_deployment.sh."
  log "INFO" "Please install gcloud and then run test_gcp_deployment.sh manually."
fi

log "SUCCESS" "GCP configuration and verification complete!"
log "INFO" "Please review the output above to ensure all steps completed successfully."
log "INFO" "For more information, see GCP_CONFIGURATION_README.md and GCP_DEPLOYMENT_VERIFICATION.md."