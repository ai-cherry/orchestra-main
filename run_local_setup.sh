#!/bin/bash
# run_local_setup.sh - Run the local setup process for the AI Orchestra project

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SECRET_MANAGER_KEY="secret-management-key.json"
PROJECT_ADMIN_KEY="project-admin-key.json"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

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
    "STEP")
      echo -e "\n${BLUE}[${timestamp}] [STEP] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "STEP" "Checking requirements..."
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  
  # Check for service account key files
  if [ ! -f "${SECRET_MANAGER_KEY}" ]; then
    log "ERROR" "Secret Manager key file not found: ${SECRET_MANAGER_KEY}"
    exit 1
  fi
  
  if [ ! -f "${PROJECT_ADMIN_KEY}" ]; then
    log "ERROR" "Project Admin key file not found: ${PROJECT_ADMIN_KEY}"
    exit 1
  fi
  
  # Check for GitHub CLI if GITHUB_TOKEN is set
  if [ -n "${GITHUB_TOKEN}" ]; then
    if ! command -v gh &> /dev/null; then
      log "WARN" "GitHub CLI not found, GitHub organization secrets will not be updated"
      log "INFO" "Please install it: https://cli.github.com/manual/installation"
    fi
  else
    log "WARN" "GITHUB_TOKEN not set, GitHub organization secrets will not be updated"
    log "INFO" "Set the GITHUB_TOKEN environment variable to update GitHub organization secrets"
  fi
  
  log "SUCCESS" "All requirements satisfied"
}

# Run the create_badass_service_keys.sh script
run_create_badass_service_keys() {
  log "STEP" "Creating powerful service account keys..."
  
  # Make sure the script is executable
  chmod +x create_badass_service_keys.sh
  
  # Run the script
  ./create_badass_service_keys.sh
  
  log "SUCCESS" "Powerful service account keys created successfully"
}

# Run the verify_gcp_setup.sh script
run_verify_gcp_setup() {
  log "STEP" "Verifying GCP setup..."
  
  # Make sure the script is executable
  chmod +x scripts/verify_gcp_setup.sh
  
  # Set the environment variables
  export GCP_PROJECT_ID="${PROJECT_ID}"
  export REGION="${REGION}"
  export GCP_MASTER_SERVICE_JSON="$(cat ${PROJECT_ADMIN_KEY})"
  
  # Run the script
  scripts/verify_gcp_setup.sh
  
  log "SUCCESS" "GCP setup verified successfully"
}

# Run the secure_exposed_credentials.sh script
run_secure_exposed_credentials() {
  log "STEP" "Securing exposed credentials..."
  
  # Make sure the script is executable
  chmod +x secure_exposed_credentials.sh
  
  # Run the script
  ./secure_exposed_credentials.sh
  
  log "SUCCESS" "Exposed credentials secured successfully"
}

# Commit changes
commit_changes() {
  log "STEP" "Committing changes..."
  
  # Check if git is available
  if ! command -v git &> /dev/null; then
    log "WARN" "git not found, changes will not be committed"
    return
  fi
  
  # Add the changes
  git add .
  
  # Commit the changes
  git commit -m "Set up GCP infrastructure for AI Orchestra project"
  
  log "SUCCESS" "Changes committed successfully"
}

# Push changes
push_changes() {
  log "STEP" "Pushing changes..."
  
  # Check if git is available
  if ! command -v git &> /dev/null; then
    log "WARN" "git not found, changes will not be pushed"
    return
  fi
  
  # Push the changes
  git push origin main
  
  log "SUCCESS" "Changes pushed successfully"
}

# Main function
main() {
  log "INFO" "Starting local setup process for the AI Orchestra project..."
  
  # Check requirements
  check_requirements
  
  # Run the create_badass_service_keys.sh script
  run_create_badass_service_keys
  
  # Run the verify_gcp_setup.sh script
  run_verify_gcp_setup
  
  # Run the secure_exposed_credentials.sh script
  run_secure_exposed_credentials
  
  # Commit changes
  commit_changes
  
  # Push changes
  push_changes
  
  log "SUCCESS" "Local setup process completed successfully!"
  log "INFO" "The AI Orchestra project is now set up with GCP infrastructure"
  log "INFO" "You can now use the GitHub Actions workflow to deploy the project"
}

# Execute main function
main