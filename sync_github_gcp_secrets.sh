#!/bin/bash
# sync_github_gcp_secrets.sh - Synchronize GitHub organization secrets with GCP Secret Manager
# This script ensures bidirectional synchronization between GitHub organization secrets and GCP Secret Manager

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${GITHUB_REPO:=orchestra-main}"

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
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if GCP_MASTER_SERVICE_JSON is provided
if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
  log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is required"
  exit 1
fi

# Check if GitHub PAT is provided
if [[ -z "${GITHUB_TOKEN}" ]]; then
  log "ERROR" "GITHUB_TOKEN environment variable is required"
  exit 1
fi

# Bootstrap with GCP_MASTER_SERVICE_JSON
log "INFO" "Authenticating with GCP using GCP_MASTER_SERVICE_JSON..."
echo "$GCP_MASTER_SERVICE_JSON" > /tmp/master-key.json
chmod 600 /tmp/master-key.json
gcloud auth activate-service-account --key-file=/tmp/master-key.json

# Verify authentication worked
if ! gcloud projects describe "${GCP_PROJECT_ID}" &>/dev/null; then
  log "ERROR" "Failed to authenticate with GCP_MASTER_SERVICE_JSON"
  rm /tmp/master-key.json
  exit 1
fi

# Authenticate with GitHub
log "INFO" "Authenticating with GitHub using GITHUB_TOKEN..."
echo "${GITHUB_TOKEN}" | gh auth login --with-token

# Verify GitHub authentication
if ! gh auth status &>/dev/null; then
  log "ERROR" "Failed to authenticate with GitHub"
  exit 1
fi

# Enable Secret Manager API if not already enabled
log "INFO" "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project="${GCP_PROJECT_ID}"

# Get list of GitHub organization secrets
log "INFO" "Retrieving GitHub organization secrets..."
GITHUB_SECRETS=$(gh secret list --org "${GITHUB_ORG}" --json name --jq '.[].name')

if [[ -z "${GITHUB_SECRETS}" ]]; then
  log "WARN" "No GitHub organization secrets found"
else
  log "INFO" "Found $(echo "${GITHUB_SECRETS}" | wc -l) GitHub organization secrets"
fi

# Create a temporary directory for secret values
TEMP_DIR=$(mktemp -d)
chmod 700 "${TEMP_DIR}"

# Process each GitHub secret
echo "${GITHUB_SECRETS}" | while read -r SECRET_NAME; do
  log "INFO" "Processing secret: ${SECRET_NAME}"
  
  # Skip certain secrets that shouldn't be synced
  if [[ "${SECRET_NAME}" == "GITHUB_TOKEN" ]]; then
    log "WARN" "Skipping GITHUB_TOKEN as it shouldn't be stored in GCP"
    continue
  fi
  
  # Format the secret name for GCP (lowercase with hyphens instead of underscores)
  GCP_SECRET_NAME=$(echo "${SECRET_NAME}" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
  
  # Check if secret already exists in GCP
  if gcloud secrets describe "${GCP_SECRET_NAME}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Secret ${GCP_SECRET_NAME} already exists in GCP Secret Manager"
  else
    # Create the secret in GCP
    log "INFO" "Creating secret ${GCP_SECRET_NAME} in GCP Secret Manager..."
    gcloud secrets create "${GCP_SECRET_NAME}" --project="${GCP_PROJECT_ID}"
  fi
  
  # For GitHub organization secrets, we need to use GitHub API to get the values
  # Since we can't directly read the values, we'll use a workaround:
  # 1. Check if the secret exists in the environment (for testing)
  # 2. If not, prompt the user to provide the value (for interactive use)
  
  if [[ -n "${!SECRET_NAME}" ]]; then
    log "INFO" "Found value for ${SECRET_NAME} in environment"
    SECRET_VALUE="${!SECRET_NAME}"
    
    # Save to temporary file
    SECRET_FILE="${TEMP_DIR}/${SECRET_NAME}"
    echo "${SECRET_VALUE}" > "${SECRET_FILE}"
    
    # Update the secret in GCP
    log "INFO" "Updating secret ${GCP_SECRET_NAME} in GCP Secret Manager..."
    gcloud secrets versions add "${GCP_SECRET_NAME}" --data-file="${SECRET_FILE}" --project="${GCP_PROJECT_ID}"
    
    # Clean up
    rm "${SECRET_FILE}"
  else
    log "WARN" "No value found for ${SECRET_NAME} in environment"
    log "INFO" "Checking if secret exists in GCP Secret Manager..."
    
    # Check if the secret already exists in GCP and has versions
    if gcloud secrets versions list "${GCP_SECRET_NAME}" --project="${GCP_PROJECT_ID}" --format="value(name)" | grep -q "^[0-9]"; then
      log "INFO" "Secret ${GCP_SECRET_NAME} exists in GCP Secret Manager with versions"
    else
      log "WARN" "Secret ${GCP_SECRET_NAME} doesn't have versions in GCP Secret Manager"
      log "INFO" "Prompting for secret value..."
      
      # Prompt for the secret value (only in interactive mode)
      if [[ -t 0 ]]; then
        read -p "Enter value for ${SECRET_NAME} (or leave empty to skip): " -s SECRET_VALUE
        echo ""
        
        if [[ -n "${SECRET_VALUE}" ]]; then
          # Save to temporary file
          SECRET_FILE="${TEMP_DIR}/${SECRET_NAME}"
          echo "${SECRET_VALUE}" > "${SECRET_FILE}"
          
          # Update the secret in GCP
          log "INFO" "Updating secret ${GCP_SECRET_NAME} in GCP Secret Manager..."
          gcloud secrets versions add "${GCP_SECRET_NAME}" --data-file="${SECRET_FILE}" --project="${GCP_PROJECT_ID}"
          
          # Clean up
          rm "${SECRET_FILE}"
        else
          log "WARN" "No value provided for ${SECRET_NAME}, skipping GCP update"
        fi
      else
        log "WARN" "Not running in interactive mode, skipping prompt for ${SECRET_NAME}"
      fi
    fi
  fi
done

# Now check for secrets in GCP that should be synced to GitHub
log "INFO" "Checking for GCP secrets to sync to GitHub..."
GCP_SECRETS=$(gcloud secrets list --project="${GCP_PROJECT_ID}" --format="value(name)")

echo "${GCP_SECRETS}" | while read -r GCP_SECRET_NAME; do
  # Format the secret name for GitHub (uppercase with underscores instead of hyphens)
  GITHUB_SECRET_NAME=$(echo "${GCP_SECRET_NAME}" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
  
  # Check if this secret already exists in GitHub
  if echo "${GITHUB_SECRETS}" | grep -q "^${GITHUB_SECRET_NAME}$"; then
    log "INFO" "Secret ${GITHUB_SECRET_NAME} already exists in GitHub"
  else
    log "INFO" "Secret ${GITHUB_SECRET_NAME} not found in GitHub, syncing from GCP..."
    
    # Get the latest version of the secret from GCP
    SECRET_VERSION=$(gcloud secrets versions list "${GCP_SECRET_NAME}" --project="${GCP_PROJECT_ID}" --format="value(name)" --limit=1)
    
    if [[ -n "${SECRET_VERSION}" ]]; then
      # Get the secret value
      SECRET_FILE="${TEMP_DIR}/${GCP_SECRET_NAME}"
      gcloud secrets versions access "${SECRET_VERSION}" --secret="${GCP_SECRET_NAME}" --project="${GCP_PROJECT_ID}" > "${SECRET_FILE}"
      
      # Create the secret in GitHub
      log "INFO" "Creating secret ${GITHUB_SECRET_NAME} in GitHub organization..."
      gh secret set "${GITHUB_SECRET_NAME}" --org "${GITHUB_ORG}" --body-file "${SECRET_FILE}"
      
      # Clean up
      rm "${SECRET_FILE}"
    else
      log "WARN" "No versions found for secret ${GCP_SECRET_NAME} in GCP"
    fi
  fi
done

# Clean up
rm -rf "${TEMP_DIR}"
rm -f /tmp/master-key.json

log "INFO" "Secret synchronization complete!"
log "INFO" "GitHub organization secrets are now synchronized with GCP Secret Manager"