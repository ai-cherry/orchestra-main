#!/bin/bash
# run_local_setup.sh - Run the infrastructure setup locally using GitHub secrets

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${GITHUB_REPO:=orchestra-main}"
: "${REGION:=us-central1}"
: "${ENV:=dev}"

# Log function with timestamps
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${GREEN}[${timestamp}] [INFO] ${message}${NC}"
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

# Check requirements
check_requirements() {
  log "INFO" "Checking requirements..."
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    log "ERROR" "GitHub CLI (gh) is required but not found"
    log "INFO" "Please install it: https://cli.github.com/manual/installation"
    exit 1
  fi
  
  # Check for GitHub PAT
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    log "INFO" "Please set it: export GITHUB_TOKEN=your_github_token"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GitHub
authenticate_github() {
  log "INFO" "Authenticating with GitHub using GITHUB_TOKEN..."
  echo "${GITHUB_TOKEN}" | gh auth login --with-token
  
  # Verify GitHub authentication
  if ! gh auth status &>/dev/null; then
    log "ERROR" "Failed to authenticate with GitHub"
    exit 1
  fi
  
  log "SUCCESS" "Successfully authenticated with GitHub"
}

# Fetch GCP_MASTER_SERVICE_JSON from GitHub secrets
fetch_gcp_master_service_json() {
  log "INFO" "Fetching GCP_MASTER_SERVICE_JSON from GitHub secrets..."
  
  # Create a temporary file to store the secret
  local temp_file=$(mktemp)
  
  # Fetch the secret
  if gh secret get GCP_MASTER_SERVICE_JSON --org "${GITHUB_ORG}" > "${temp_file}" 2>/dev/null; then
    log "SUCCESS" "Successfully fetched GCP_MASTER_SERVICE_JSON from GitHub secrets"
  else
    log "ERROR" "Failed to fetch GCP_MASTER_SERVICE_JSON from GitHub secrets"
    rm -f "${temp_file}"
    exit 1
  fi
  
  # Return the path to the temporary file
  echo "${temp_file}"
}

# Run setup_gcp_infrastructure.sh
run_setup_gcp_infrastructure() {
  log "INFO" "Running setup_gcp_infrastructure.sh..."
  
  # Check if the script exists
  if [ ! -f "setup_gcp_infrastructure.sh" ]; then
    log "ERROR" "setup_gcp_infrastructure.sh not found"
    exit 1
  fi
  
  # Make the script executable
  chmod +x setup_gcp_infrastructure.sh
  
  # Run the script
  GCP_MASTER_SERVICE_JSON=$(cat "$1") \
  GITHUB_TOKEN="${GITHUB_TOKEN}" \
  GCP_PROJECT_ID="${GCP_PROJECT_ID}" \
  GITHUB_ORG="${GITHUB_ORG}" \
  GITHUB_REPO="${GITHUB_REPO}" \
  REGION="${REGION}" \
  ENV="${ENV}" \
  ./setup_gcp_infrastructure.sh
  
  log "SUCCESS" "setup_gcp_infrastructure.sh completed successfully"
}

# Run update_gcp_infrastructure.sh
run_update_gcp_infrastructure() {
  log "INFO" "Running update_gcp_infrastructure.sh..."
  
  # Check if the script exists
  if [ ! -f "update_gcp_infrastructure.sh" ]; then
    log "ERROR" "update_gcp_infrastructure.sh not found"
    exit 1
  fi
  
  # Make the script executable
  chmod +x update_gcp_infrastructure.sh
  
  # Run the script
  GCP_MASTER_SERVICE_JSON=$(cat "$1") \
  GITHUB_TOKEN="${GITHUB_TOKEN}" \
  GCP_PROJECT_ID="${GCP_PROJECT_ID}" \
  GITHUB_ORG="${GITHUB_ORG}" \
  GITHUB_REPO="${GITHUB_REPO}" \
  REGION="${REGION}" \
  ENV="${ENV}" \
  ./update_gcp_infrastructure.sh
  
  log "SUCCESS" "update_gcp_infrastructure.sh completed successfully"
}

# Run verify_gcp_setup.sh
run_verify_gcp_setup() {
  log "INFO" "Running verify_gcp_setup.sh..."
  
  # Check if the script exists
  if [ ! -f "scripts/verify_gcp_setup.sh" ]; then
    log "ERROR" "scripts/verify_gcp_setup.sh not found"
    exit 1
  fi
  
  # Make the script executable
  chmod +x scripts/verify_gcp_setup.sh
  
  # Run the script
  GCP_MASTER_SERVICE_JSON=$(cat "$1") \
  GCP_PROJECT_ID="${GCP_PROJECT_ID}" \
  REGION="${REGION}" \
  ./scripts/verify_gcp_setup.sh
  
  log "SUCCESS" "verify_gcp_setup.sh completed successfully"
}

# Clean up temporary files
cleanup() {
  log "INFO" "Cleaning up temporary files..."
  
  # Remove the temporary file
  rm -f "$1"
  
  log "SUCCESS" "Temporary files cleaned up"
}

# Main function
main() {
  log "INFO" "Starting local infrastructure setup..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Fetch GCP_MASTER_SERVICE_JSON from GitHub secrets
  local master_key_file=$(fetch_gcp_master_service_json)
  
  # Run setup_gcp_infrastructure.sh
  run_setup_gcp_infrastructure "${master_key_file}"
  
  # Run update_gcp_infrastructure.sh
  run_update_gcp_infrastructure "${master_key_file}"
  
  # Run verify_gcp_setup.sh
  run_verify_gcp_setup "${master_key_file}"
  
  # Clean up temporary files
  cleanup "${master_key_file}"
  
  log "SUCCESS" "Local infrastructure setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Fetched GCP_MASTER_SERVICE_JSON from GitHub secrets"
  log "INFO" "2. Ran setup_gcp_infrastructure.sh to set up the GCP infrastructure"
  log "INFO" "3. Ran update_gcp_infrastructure.sh to update GitHub secrets"
  log "INFO" "4. Ran verify_gcp_setup.sh to verify the GCP setup"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Create a new Codespace or rebuild an existing one"
  log "INFO" "2. Verify that the Codespace has access to GCP resources"
}

# Execute main function
main