#!/bin/bash
# update_github_org_secrets.sh - Update GitHub organization secrets with GCP service account keys

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
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please install it: https://cloud.google.com/sdk/docs/install"
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

# Authenticate with GCP
authenticate_gcp() {
  log "INFO" "Authenticating with GCP..."
  
  # Check if GCP_MASTER_SERVICE_JSON is set
  if [[ -n "${GCP_MASTER_SERVICE_JSON}" ]]; then
    # Create a temporary file for the service account key
    local temp_file=$(mktemp)
    echo "${GCP_MASTER_SERVICE_JSON}" > "${temp_file}"
    
    # Authenticate with the service account key
    gcloud auth activate-service-account --key-file="${temp_file}"
    
    # Clean up
    rm -f "${temp_file}"
  else
    log "WARN" "GCP_MASTER_SERVICE_JSON not set, using default authentication"
    # Use default authentication (Application Default Credentials)
    gcloud auth application-default login --no-launch-browser
  fi
  
  # Set the project
  gcloud config set project "${GCP_PROJECT_ID}"
  
  log "SUCCESS" "Successfully authenticated with GCP"
}

# Get service account key from Secret Manager
get_service_account_key() {
  local secret_name=$1
  
  log "INFO" "Getting service account key from Secret Manager: ${secret_name}..."
  
  # Get the latest version of the secret
  local secret_value=$(gcloud secrets versions access latest --secret="${secret_name}" --project="${GCP_PROJECT_ID}")
  
  echo "${secret_value}"
}

# Update GitHub organization secret
update_github_org_secret() {
  local secret_name=$1
  local secret_value=$2
  
  log "INFO" "Updating GitHub organization secret: ${secret_name}..."
  
  # Update the secret
  echo "${secret_value}" | gh secret set "${secret_name}" --org "${GITHUB_ORG}"
  
  log "SUCCESS" "Successfully updated GitHub organization secret: ${secret_name}"
}

# Update GitHub repository secret
update_github_repo_secret() {
  local secret_name=$1
  local secret_value=$2
  
  log "INFO" "Updating GitHub repository secret: ${secret_name}..."
  
  # Update the secret
  echo "${secret_value}" | gh secret set "${secret_name}" --repo "${GITHUB_ORG}/${GITHUB_REPO}"
  
  log "SUCCESS" "Successfully updated GitHub repository secret: ${secret_name}"
}

# Main function
main() {
  log "INFO" "Starting GitHub organization secrets update..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Update GitHub organization secrets
  
  # 1. GCP_PROJECT_ID
  log "INFO" "Updating GCP_PROJECT_ID secret..."
  update_github_org_secret "GCP_PROJECT_ID" "${GCP_PROJECT_ID}"
  
  # 2. GCP_REGION
  log "INFO" "Updating GCP_REGION secret..."
  update_github_org_secret "GCP_REGION" "${REGION}"
  
  # 3. GCP_MASTER_SERVICE_JSON
  log "INFO" "Updating GCP_MASTER_SERVICE_JSON secret..."
  local master_key=$(get_service_account_key "master-service-account-key")
  update_github_org_secret "GCP_MASTER_SERVICE_JSON" "${master_key}"
  
  # 4. GCP_VERTEX_POWER_KEY
  log "INFO" "Updating GCP_VERTEX_POWER_KEY secret..."
  local vertex_key=$(get_service_account_key "vertex-power-key")
  update_github_org_secret "GCP_VERTEX_POWER_KEY" "${vertex_key}"
  
  # 5. GCP_GEMINI_POWER_KEY
  log "INFO" "Updating GCP_GEMINI_POWER_KEY secret..."
  local gemini_key=$(get_service_account_key "gemini-power-key")
  update_github_org_secret "GCP_GEMINI_POWER_KEY" "${gemini_key}"
  
  # 6. GCP_PROJECT_NUMBER
  log "INFO" "Getting GCP project number..."
  local project_number=$(gcloud projects describe "${GCP_PROJECT_ID}" --format="value(projectNumber)")
  update_github_org_secret "GCP_PROJECT_NUMBER" "${project_number}"
  
  # 7. GCP_WORKLOAD_IDENTITY_PROVIDER
  log "INFO" "Getting Workload Identity Provider..."
  local wif_provider="projects/${project_number}/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider"
  update_github_org_secret "GCP_WORKLOAD_IDENTITY_PROVIDER" "${wif_provider}"
  
  # 8. GCP_SERVICE_ACCOUNT
  log "INFO" "Updating GCP_SERVICE_ACCOUNT secret..."
  local service_account="github-actions@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  update_github_org_secret "GCP_SERVICE_ACCOUNT" "${service_account}"
  
  log "SUCCESS" "GitHub organization secrets updated successfully!"
}

# Execute main function
main
