#!/bin/bash

# Script to create service accounts with appropriate permissions for Vertex AI and Gemini,
# generate keys, and update GitHub organization secrets

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

# Create service account for Vertex AI with all necessary permissions
create_vertex_service_account() {
  step "Creating Vertex AI service account with comprehensive permissions"
  
  # Service account details
  SA_NAME="vertex-ai-admin"
  SA_DISPLAY_NAME="Vertex AI Administration Service Account"
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
  
  # Vertex AI roles
  VERTEX_ROLES=(
    # Core Vertex AI roles
    "roles/aiplatform.admin"                    # Full control over Vertex AI resources
    "roles/aiplatform.user"                     # Use Vertex AI resources
    "roles/aiplatform.serviceAgent"             # Service agent role
    
    # ML, storage, and model registry roles
    "roles/ml.admin"                           # Admin for ML Engine
    "roles/storage.admin"                      # Manage Cloud Storage for model artifacts
    "roles/artifactregistry.admin"             # Manage Artifact Registry for models
    
    # Compute and operations roles
    "roles/compute.admin"                      # Manage Compute Engine resources
    "roles/logging.admin"                      # Access to logging
    "roles/monitoring.admin"                   # Access to monitoring
    
    # Gemini-specific roles
    "roles/aiplatform.serviceAgent"            # Gemini service agent role
    "roles/serviceusage.serviceUsageConsumer"  # Service usage consumer for API activation
  )
  
  # Grant roles to the service account
  for ROLE in "${VERTEX_ROLES[@]}"; do
    log "Granting ${ROLE} to ${SA_EMAIL}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${ROLE}" \
      --no-user-output-enabled
  done
  
  # Create key for service account
  log "Creating key for Vertex AI service account..."
  VERTEX_KEY_FILE="vertex-ai-admin-key.json"
  gcloud iam service-accounts keys create "${VERTEX_KEY_FILE}" \
    --iam-account="${SA_EMAIL}" \
    --project="${PROJECT_ID}"
  
  # Format key for GitHub secrets (JSON as single line with escaped quotes)
  VERTEX_KEY_CONTENT=$(cat "${VERTEX_KEY_FILE}" | tr -d '\n' | sed 's/"/\\"/g')
  
  log "Vertex AI service account and key created successfully."
  
  # Return the key content
  echo "${VERTEX_KEY_CONTENT}"
}

# Create service account for Secret Management with all necessary permissions
create_secret_mgmt_service_account() {
  step "Creating Secret Management service account"
  
  # Service account details
  SA_NAME="secret-management-admin"
  SA_DISPLAY_NAME="Secret Management Service Account"
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
  
  # Secret management roles
  SECRET_ROLES=(
    "roles/secretmanager.admin"                # Secret Manager admin
    "roles/secretmanager.secretAccessor"       # Access secrets
    "roles/secretmanager.secretVersionManager" # Manage secret versions
    "roles/iam.serviceAccountTokenCreator"     # Create service account tokens
    "roles/iam.serviceAccountKeyAdmin"         # Manage service account keys
  )
  
  # Grant roles to the service account
  for ROLE in "${SECRET_ROLES[@]}"; do
    log "Granting ${ROLE} to ${SA_EMAIL}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${ROLE}" \
      --no-user-output-enabled
  done
  
  # Create key for service account
  log "Creating key for Secret Management service account..."
  SECRET_KEY_FILE="secret-mgmt-admin-key.json"
  gcloud iam service-accounts keys create "${SECRET_KEY_FILE}" \
    --iam-account="${SA_EMAIL}" \
    --project="${PROJECT_ID}"
  
  # Format key for GitHub secrets (JSON as single line with escaped quotes)
  SECRET_KEY_CONTENT=$(cat "${SECRET_KEY_FILE}" | tr -d '\n' | sed 's/"/\\"/g')
  
  log "Secret Management service account and key created successfully."
  
  # Return the key content
  echo "${SECRET_KEY_CONTENT}"
}

# Update GitHub organization secrets
update_github_secrets() {
  step "Updating GitHub organization secrets"
  
  VERTEX_KEY="$1"
  SECRET_KEY="$2"
  
  # Define secrets to update
  declare -A SECRETS=(
    ["GCP_PROJECT_ID"]="${PROJECT_ID}"
    ["GCP_PROJECT_NAME"]="${PROJECT_NAME}"
    ["GCP_PROJECT_ADMIN_KEY"]="${VERTEX_KEY}"
    ["GCP_SECRET_MANAGEMENT_KEY"]="${SECRET_KEY}"
    ["GCP_VERTEX_AI_ADMIN_KEY"]="${VERTEX_KEY}"  # Adding duplicate for explicit naming
    ["GCP_GEMINI_API_KEY"]="${VERTEX_KEY}"       # Same key for simplicity in this initial setup
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
  
  log "All GitHub organization secrets have been updated."
}

# Check if required APIs are enabled, enable if needed
ensure_apis_enabled() {
  step "Ensuring required APIs are enabled"
  
  REQUIRED_APIS=(
    "aiplatform.googleapis.com"      # Vertex AI API
    "artifactregistry.googleapis.com" # Artifact Registry API
    "secretmanager.googleapis.com"    # Secret Manager API
    "iam.googleapis.com"              # IAM API
    "cloudresourcemanager.googleapis.com" # Resource Manager API
  )
  
  for API in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --project="${PROJECT_ID}" --filter="name:${API}" --format="value(name)" | grep -q "${API}"; then
      log "Enabling ${API}..."
      gcloud services enable "${API}" --project="${PROJECT_ID}"
    else
      log "${API} is already enabled."
    fi
  done
  
  log "All required APIs are enabled."
}

# Main execution
main() {
  log "Starting service account creation and GitHub secret update process"
  
  prompt_project_info
  validate_gcloud
  ensure_apis_enabled
  
  VERTEX_KEY=$(create_vertex_service_account)
  SECRET_KEY=$(create_secret_mgmt_service_account)
  
  update_github_secrets "${VERTEX_KEY}" "${SECRET_KEY}"
  
  # Clean up key files
  if [ -f "vertex-ai-admin-key.json" ]; then
    log "Removing local key file: vertex-ai-admin-key.json"
    rm -f "vertex-ai-admin-key.json"
  fi
  
  if [ -f "secret-mgmt-admin-key.json" ]; then
    log "Removing local key file: secret-mgmt-admin-key.json"
    rm -f "secret-mgmt-admin-key.json"
  fi
  
  log "Service account creation and GitHub secret update completed successfully!"
  log "GitHub organization ${GITHUB_ORG} now has the following secrets set:"
  log "- GCP_PROJECT_ID"
  log "- GCP_PROJECT_NAME"
  log "- GCP_PROJECT_ADMIN_KEY (Vertex AI admin service account key)"
  log "- GCP_SECRET_MANAGEMENT_KEY (Secret Management service account key)"
  log "- GCP_VERTEX_AI_ADMIN_KEY (same as PROJECT_ADMIN_KEY for specific usage)"
  log "- GCP_GEMINI_API_KEY (same as PROJECT_ADMIN_KEY for now)"
}

# Execute the script
main
