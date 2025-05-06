#!/bin/bash
# create_powerful_service_keys.sh - Create powerful service keys for Vertex AI and Gemini
# This script creates service account keys with extensive permissions for AI services

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
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "INFO" "Checking requirements..."
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please ensure the Google Cloud SDK is installed and in your PATH"
    exit 1
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    log "WARN" "GitHub CLI not found. GitHub secrets will not be updated automatically"
    log "WARN" "You will need to manually set the GitHub secrets"
  fi
  
  # Check for GCP_MASTER_SERVICE_JSON
  if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is required"
    exit 1
  fi
  
  # Check for GitHub PAT
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GCP using the master service account key
authenticate_gcp() {
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
  
  log "INFO" "Successfully authenticated with GCP"
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
  
  log "INFO" "Successfully authenticated with GitHub"
}

# Enable required GCP APIs
enable_apis() {
  log "INFO" "Enabling required APIs..."
  gcloud services enable iamcredentials.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    --project "${GCP_PROJECT_ID}"
  
  log "INFO" "APIs enabled successfully"
}

# Create Vertex AI service account with powerful permissions
create_vertex_service_account() {
  local sa_name="vertex-power-user"
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  log "INFO" "Creating Vertex AI service account: ${sa_email}"
  
  # Create service account if it doesn't exist
  if gcloud iam service-accounts describe "${sa_email}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Service account ${sa_email} already exists"
  else
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="Vertex AI Power User" \
      --description="Service account with extensive permissions for Vertex AI operations" \
      --project="${GCP_PROJECT_ID}"
    log "INFO" "Service account ${sa_email} created successfully"
  fi
  
  # Grant powerful roles to the service account
  log "INFO" "Granting roles to ${sa_email}"
  
  # List of roles to grant
  local roles=(
    "roles/aiplatform.admin"
    "roles/aiplatform.user"
    "roles/storage.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/iam.serviceAccountTokenCreator"
    "roles/compute.admin"
    "roles/serviceusage.serviceUsageAdmin"
  )
  
  for role in "${roles[@]}"; do
    log "INFO" "Granting ${role} to ${sa_email}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${sa_email}" \
      --role="${role}"
  done
  
  # Create and download service account key
  log "INFO" "Creating service account key for ${sa_email}"
  gcloud iam service-accounts keys create "/tmp/vertex-key.json" \
    --iam-account="${sa_email}" \
    --project="${GCP_PROJECT_ID}"
  
  # Store key in Secret Manager
  log "INFO" "Storing Vertex AI key in Secret Manager"
  if gcloud secrets describe "vertex-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "vertex-power-key" \
      --data-file="/tmp/vertex-key.json" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "vertex-power-key" \
      --data-file="/tmp/vertex-key.json" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Save key content for GitHub secrets
  VERTEX_KEY=$(cat /tmp/vertex-key.json)
  
  log "INFO" "Vertex AI service account setup complete"
}

# Create Gemini service account with powerful permissions
create_gemini_service_account() {
  local sa_name="gemini-power-user"
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  log "INFO" "Creating Gemini service account: ${sa_email}"
  
  # Create service account if it doesn't exist
  if gcloud iam service-accounts describe "${sa_email}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Service account ${sa_email} already exists"
  else
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="Gemini Power User" \
      --description="Service account with extensive permissions for Gemini operations" \
      --project="${GCP_PROJECT_ID}"
    log "INFO" "Service account ${sa_email} created successfully"
  fi
  
  # Grant powerful roles to the service account
  log "INFO" "Granting roles to ${sa_email}"
  
  # List of roles to grant
  local roles=(
    "roles/aiplatform.admin"
    "roles/aiplatform.user"
    "roles/storage.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/iam.serviceAccountTokenCreator"
    "roles/serviceusage.serviceUsageAdmin"
  )
  
  for role in "${roles[@]}"; do
    log "INFO" "Granting ${role} to ${sa_email}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${sa_email}" \
      --role="${role}"
  done
  
  # Create and download service account key
  log "INFO" "Creating service account key for ${sa_email}"
  gcloud iam service-accounts keys create "/tmp/gemini-key.json" \
    --iam-account="${sa_email}" \
    --project="${GCP_PROJECT_ID}"
  
  # Store key in Secret Manager
  log "INFO" "Storing Gemini key in Secret Manager"
  if gcloud secrets describe "gemini-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "gemini-power-key" \
      --data-file="/tmp/gemini-key.json" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "gemini-power-key" \
      --data-file="/tmp/gemini-key.json" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Save key content for GitHub secrets
  GEMINI_KEY=$(cat /tmp/gemini-key.json)
  
  log "INFO" "Gemini service account setup complete"
}

# Update GitHub organization secrets
update_github_secrets() {
  log "INFO" "Updating GitHub organization secrets..."
  
  if ! command -v gh &> /dev/null; then
    log "WARN" "GitHub CLI not found. Skipping GitHub secret updates"
    log "WARN" "You will need to manually set the following secrets in your GitHub organization:"
    log "WARN" "  - GCP_VERTEX_POWER_KEY: <content of /tmp/vertex-key.json>"
    log "WARN" "  - GCP_GEMINI_POWER_KEY: <content of /tmp/gemini-key.json>"
    log "WARN" "  - GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
    log "WARN" "  - GCP_REGION: ${REGION}"
    return
  fi
  
  # Set the GCP_VERTEX_POWER_KEY secret
  log "INFO" "Setting GCP_VERTEX_POWER_KEY secret"
  echo "${VERTEX_KEY}" | gh secret set "GCP_VERTEX_POWER_KEY" --org "${GITHUB_ORG}" --body -
  
  # Set the GCP_GEMINI_POWER_KEY secret
  log "INFO" "Setting GCP_GEMINI_POWER_KEY secret"
  echo "${GEMINI_KEY}" | gh secret set "GCP_GEMINI_POWER_KEY" --org "${GITHUB_ORG}" --body -
  
  # Set the GCP_PROJECT_ID secret
  log "INFO" "Setting GCP_PROJECT_ID secret to: ${GCP_PROJECT_ID}"
  gh secret set "GCP_PROJECT_ID" --org "${GITHUB_ORG}" --body "${GCP_PROJECT_ID}"
  
  # Set the GCP_REGION secret
  log "INFO" "Setting GCP_REGION secret to: ${REGION}"
  gh secret set "GCP_REGION" --org "${GITHUB_ORG}" --body "${REGION}"
  
  log "INFO" "GitHub organization secrets updated successfully"
}

# Clean up temporary files
cleanup() {
  log "INFO" "Cleaning up temporary files..."
  rm -f /tmp/master-key.json
  rm -f /tmp/vertex-key.json
  rm -f /tmp/gemini-key.json
  
  log "INFO" "Cleanup complete"
}

# Main function
main() {
  log "INFO" "Starting powerful service key setup for AI Orchestra..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Authenticate with GitHub
  authenticate_github
  
  # Enable required APIs
  enable_apis
  
  # Create Vertex AI service account and key
  create_vertex_service_account
  
  # Create Gemini service account and key
  create_gemini_service_account
  
  # Update GitHub secrets
  update_github_secrets
  
  # Clean up
  cleanup
  
  log "INFO" "Service key setup complete!"
  log "INFO" "Vertex AI service account: vertex-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  log "INFO" "Gemini service account: gemini-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Use these service accounts in your GitHub workflows"
  log "INFO" "2. Configure Codespaces to use these service accounts"
  log "INFO" "3. Test the integration between GitHub, Codespaces, and GCP"
}

# Execute main function
main