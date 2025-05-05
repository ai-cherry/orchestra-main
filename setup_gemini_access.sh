#!/bin/bash

# Script to create a service account with Gemini API permissions and update GitHub organization secrets
# This script specifically focuses on setting up access for Gemini Cloud Assist, Gemini Code Assist, and related services

set -e

# Color codes for better readability
RESET="\033[0m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"

# GitHub settings
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Project settings (will be prompted if not set)
PROJECT_ID=""
PROJECT_NAME=""

# Log a message with timestamp
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${RESET}"
}

# Log a warning message
warn() {
  echo -e "${YELLOW}[WARNING] $1${RESET}"
}

# Log an error message
error() {
  echo -e "${RED}[ERROR] $1${RESET}"
}

# Log a step message
step() {
  echo -e "${BLUE}==> $1${RESET}"
}

# Prompt for project information if not provided
prompt_project_info() {
  if [ -z "$PROJECT_ID" ]; then
    read -p "Enter your GCP Project ID: " PROJECT_ID
  fi

  if [ -z "$PROJECT_NAME" ]; then
    read -p "Enter your GCP Project Name: " PROJECT_NAME
  fi
}

# Validate that gcloud is properly configured
validate_gcloud() {
  step "Validating gcloud configuration"
  
  if ! command -v gcloud &> /dev/null; then
    error "gcloud command not found. Please install Google Cloud SDK."
    exit 1
  fi
  
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    error "No active gcloud account found. Please run 'gcloud auth login' first."
    exit 1
  fi
  
  log "gcloud is properly configured."
}

# Create service account for Gemini with all necessary permissions
create_gemini_service_account() {
  step "Creating Gemini service account with comprehensive permissions"
  
  # Service account details
  SA_NAME="gemini-api-admin"
  SA_DISPLAY_NAME="Gemini API Administration Service Account"
  SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
  
  # Create service account if it doesn't exist
  if ! gcloud iam service-accounts describe "${SA_EMAIL}" &>/dev/null; then
    log "Creating service account ${SA_EMAIL}..."
    gcloud iam service-accounts create "${SA_NAME}" \
      --display-name="${SA_DISPLAY_NAME}" \
      --project="${PROJECT_ID}"
  else
    log "Service account ${SA_EMAIL} already exists."
  fi
  
  # Gemini & AI-specific roles
  GEMINI_ROLES=(
    # Core Vertex AI roles for Gemini capabilities
    "roles/aiplatform.admin"                    # Full control over AI Platform resources (includes Gemini)
    "roles/aiplatform.user"                     # Use AI Platform resources
    "roles/serviceusage.serviceUsageConsumer"   # Service usage consumer for API activation
    "roles/cloudkms.admin"                      # Key management for API keys
    "roles/secretmanager.admin"                 # Secret management for API keys
    "roles/iam.serviceAccountUser"              # Service account user role
    "roles/storage.admin"                       # Needed for model storage and data processing
    "roles/servicemanagement.admin"             # Service management for API activation
    "roles/billing.projectManager"              # Required to check and manage billing for API usage
    "roles/monitoring.admin"                    # For monitoring Gemini API usage and performance
    "roles/logging.admin"                       # For logging related to Gemini operations
  )
  
  # Grant roles to the service account
  for ROLE in "${GEMINI_ROLES[@]}"; do
    log "Granting ${ROLE} to ${SA_EMAIL}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${ROLE}" \
      --no-user-output-enabled
  done
  
  # Create key for service account
  log "Creating key for Gemini service account..."
  GEMINI_KEY_FILE="gemini-api-admin-key.json"
  gcloud iam service-accounts keys create "${GEMINI_KEY_FILE}" \
    --iam-account="${SA_EMAIL}" \
    --project="${PROJECT_ID}"
  
  # Format key for GitHub secrets (JSON as single line with escaped quotes)
  GEMINI_KEY_CONTENT=$(cat "${GEMINI_KEY_FILE}" | tr -d '\n' | sed 's/"/\\"/g')
  
  log "Gemini service account and key created successfully."
  
  # Return the key content
  echo "${GEMINI_KEY_CONTENT}"
}

# Update GitHub organization secrets specifically for Gemini
update_github_secrets() {
  step "Updating GitHub organization secrets for Gemini access"
  
  GEMINI_KEY="$1"
  
  # Define secrets to update
  declare -A SECRETS=(
    ["GCP_GEMINI_API_KEY"]="${GEMINI_KEY}"
    ["GCP_GEMINI_CODE_ASSIST_KEY"]="${GEMINI_KEY}"
    ["GCP_GEMINI_CLOUD_ASSIST_KEY"]="${GEMINI_KEY}"
    ["GCP_PROJECT_ID"]="${PROJECT_ID}"
    ["GCP_PROJECT_NAME"]="${PROJECT_NAME}"
  )
  
  # Set up GitHub API authentication
  GITHUB_AUTH_HEADER="Authorization: token ${GITHUB_PAT}"
  GITHUB_API_URL="https://api.github.com"
  
  # Get public key for the organization
  log "Getting GitHub organization public key for secret encryption..."
  ORG_KEY_RESPONSE=$(curl -s -H "${GITHUB_AUTH_HEADER}" "${GITHUB_API_URL}/orgs/${GITHUB_ORG}/actions/secrets/public-key")
  
  if echo "${ORG_KEY_RESPONSE}" | grep -q "message"; then
    error "Failed to get organization public key: $(echo ${ORG_KEY_RESPONSE} | jq -r '.message')"
    exit 1
  fi
  
  ORG_KEY_ID=$(echo "${ORG_KEY_RESPONSE}" | jq -r '.key_id')
  ORG_KEY=$(echo "${ORG_KEY_RESPONSE}" | jq -r '.key')
  
  # Update each secret
  for SECRET_NAME in "${!SECRETS[@]}"; do
    SECRET_VALUE="${SECRETS[$SECRET_NAME]}"
    
    log "Updating GitHub organization secret: ${SECRET_NAME}..."
    
    # URL-safe base64 encoding (using Python as it's likely available)
    ENCODED_SECRET=$(echo -n "${SECRET_VALUE}" | python3 -c "import base64, sys; print(base64.b64encode(sys.stdin.buffer.read()).decode().replace('+', '-').replace('/', '_').rstrip('='))")
    
    # Create/update secret in the organization
    RESPONSE=$(curl -s -X PUT \
      -H "${GITHUB_AUTH_HEADER}" \
      -H "Accept: application/vnd.github.v3+json" \
      -d "{\"encrypted_value\":\"${ENCODED_SECRET}\",\"key_id\":\"${ORG_KEY_ID}\",\"visibility\":\"all\"}" \
      "${GITHUB_API_URL}/orgs/${GITHUB_ORG}/actions/secrets/${SECRET_NAME}")
    
    if echo "${RESPONSE}" | grep -q "message"; then
      error "Failed to update secret ${SECRET_NAME}: $(echo ${RESPONSE} | jq -r '.message')"
    else
      log "Secret ${SECRET_NAME} updated successfully."
    fi
  done
  
  log "All GitHub organization secrets for Gemini have been updated."
}

# Enable Gemini-related APIs
enable_gemini_apis() {
  step "Enabling Gemini-related APIs"
  
  GEMINI_APIS=(
    "aiplatform.googleapis.com"             # Vertex AI API (includes Gemini capabilities)
    "discoveryengine.googleapis.com"        # Discovery Engine API (for search capabilities)
    "serviceusage.googleapis.com"           # Service Usage API
    "cloudkms.googleapis.com"               # Cloud KMS API
    "secretmanager.googleapis.com"          # Secret Manager API
  )
  
  for API in "${GEMINI_APIS[@]}"; do
    if ! gcloud services list --project="${PROJECT_ID}" --filter="name:${API}" --format="value(name)" | grep -q "${API}"; then
      log "Enabling ${API}..."
      gcloud services enable "${API}" --project="${PROJECT_ID}"
    else
      log "${API} is already enabled."
    fi
  done
  
  log "All Gemini-related APIs are enabled."
}

# Main execution
main() {
  log "Starting Gemini service account creation and GitHub secret update process"
  
  prompt_project_info
  validate_gcloud
  enable_gemini_apis
  
  GEMINI_KEY=$(create_gemini_service_account)
  update_github_secrets "${GEMINI_KEY}"
  
  # Clean up key file
  if [ -f "gemini-api-admin-key.json" ]; then
    log "Removing local key file: gemini-api-admin-key.json"
    rm -f "gemini-api-admin-key.json"
  fi
  
  log "Gemini service account creation and GitHub secret update completed successfully!"
  log "GitHub organization ${GITHUB_ORG} now has the following Gemini-related secrets set:"
  log "- GCP_GEMINI_API_KEY"
  log "- GCP_GEMINI_CODE_ASSIST_KEY"
  log "- GCP_GEMINI_CLOUD_ASSIST_KEY"
  log "- GCP_PROJECT_ID"
  log "- GCP_PROJECT_NAME"
  log ""
  log "These keys can be used to authenticate with Gemini services including:"
  log "- Gemini API"
  log "- Gemini Code Assist"
  log "- Gemini Cloud Assist"
}

# Execute the script
main
