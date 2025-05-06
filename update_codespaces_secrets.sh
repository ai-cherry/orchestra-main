#!/bin/bash

# Script to update GitHub Codespaces secrets with GCP authentication credentials
# This ensures that developers working in Codespaces have the necessary environment variables

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

# Get values of GitHub organization secrets
get_github_org_secrets() {
  step "Retrieving existing GitHub organization secrets"
  
  # Set up GitHub API authentication
  GITHUB_AUTH_HEADER="Authorization: token ${GITHUB_PAT}"
  GITHUB_API_URL="https://api.github.com"
  
  # List of secrets we want to retrieve
  SECRETS_TO_GET=(
    "GCP_PROJECT_ID"
    "GCP_PROJECT_NAME"
    "GCP_PROJECT_ADMIN_KEY"
    "GCP_SECRET_MANAGEMENT_KEY"
    "GCP_VERTEX_AI_ADMIN_KEY"
    "GCP_GEMINI_API_KEY"
    "GCP_GEMINI_CODE_ASSIST_KEY"
    "GCP_GEMINI_CLOUD_ASSIST_KEY"
  )
  
  # Create an empty associative array to store secret names and their values
  declare -A SECRET_VALUES
  
  # Check if secrets exist and mark them
  SECRETS_RESPONSE=$(curl -s -H "${GITHUB_AUTH_HEADER}" \
    "${GITHUB_API_URL}/orgs/${GITHUB_ORG}/actions/secrets")
  
  if echo "${SECRETS_RESPONSE}" | grep -q "message"; then
    error "Failed to get list of organization secrets: $(echo ${SECRETS_RESPONSE} | jq -r '.message')"
    exit 1
  fi
  
  for SECRET_NAME in "${SECRETS_TO_GET[@]}"; do
    if echo "${SECRETS_RESPONSE}" | jq -e ".secrets[] | select(.name == \"${SECRET_NAME}\")" > /dev/null; then
      log "Secret ${SECRET_NAME} exists in organization."
      SECRET_VALUES["${SECRET_NAME}"]="PLACEHOLDER_EXISTS"
    else
      warn "Secret ${SECRET_NAME} does not exist in organization. It will be skipped."
      SECRET_VALUES["${SECRET_NAME}"]=""
    fi
  done
  
  # If project info wasn't set, get it from secrets if available
  if [ -z "$PROJECT_ID" ] && [ "${SECRET_VALUES["GCP_PROJECT_ID"]}" == "PLACEHOLDER_EXISTS" ]; then
    log "Using GCP_PROJECT_ID from organization secrets"
    PROJECT_ID="USE_FROM_SECRET"
  fi
  
  if [ -z "$PROJECT_NAME" ] && [ "${SECRET_VALUES["GCP_PROJECT_NAME"]}" == "PLACEHOLDER_EXISTS" ]; then
    log "Using GCP_PROJECT_NAME from organization secrets"
    PROJECT_NAME="USE_FROM_SECRET"
  fi
  
  echo "${SECRET_VALUES[@]}"
}

# Update GitHub Codespaces secrets
update_codespaces_secrets() {
  step "Updating GitHub Codespaces secrets"
  
  # Set up GitHub API authentication
  GITHUB_AUTH_HEADER="Authorization: token ${GITHUB_PAT}"
  GITHUB_API_URL="https://api.github.com"
  
  # Get public key for the organization's codespaces
  log "Getting GitHub organization codespaces public key for secret encryption..."
  ORG_CODESPACES_KEY_RESPONSE=$(curl -s -H "${GITHUB_AUTH_HEADER}" \
    "${GITHUB_API_URL}/orgs/${GITHUB_ORG}/codespaces/secrets/public-key")
  
  if echo "${ORG_CODESPACES_KEY_RESPONSE}" | grep -q "message"; then
    error "Failed to get organization codespaces public key: $(echo ${ORG_CODESPACES_KEY_RESPONSE} | jq -r '.message')"
    exit 1
  fi
  
  ORG_CODESPACES_KEY_ID=$(echo "${ORG_CODESPACES_KEY_RESPONSE}" | jq -r '.key_id')
  ORG_CODESPACES_KEY=$(echo "${ORG_CODESPACES_KEY_RESPONSE}" | jq -r '.key')
  
  # Get the existing secrets from org level
  declare -A SECRET_VALUES
  SECRET_VALUES_STRING=$(get_github_org_secrets)
  
  # Define codespaces-specific env var names that map to org secrets
  declare -A CODESPACES_SECRETS=(
    ["GCP_PROJECT_ID"]="PROJECT_ID"
    ["GCP_PROJECT_NAME"]="PROJECT_NAME"
    ["GOOGLE_CLOUD_PROJECT"]="PROJECT_ID"
    ["GOOGLE_APPLICATION_CREDENTIALS"]="GCP_PROJECT_ADMIN_KEY"
    ["VERTEX_AI_KEY"]="GCP_VERTEX_AI_ADMIN_KEY"
    ["GEMINI_API_KEY"]="GCP_GEMINI_API_KEY"
    ["GEMINI_CODE_ASSIST_KEY"]="GCP_GEMINI_CODE_ASSIST_KEY"
    ["GEMINI_CLOUD_ASSIST_KEY"]="GCP_GEMINI_CLOUD_ASSIST_KEY"
    ["SECRET_MANAGER_KEY"]="GCP_SECRET_MANAGEMENT_KEY"
  )
  
  # Update each codespaces secret
  for CODESPACES_SECRET_NAME in "${!CODESPACES_SECRETS[@]}"; do
    ORG_SECRET_NAME="${CODESPACES_SECRETS[$CODESPACES_SECRET_NAME]}"
    
    if [[ "${SECRET_VALUES_STRING}" == *"${ORG_SECRET_NAME} PLACEHOLDER_EXISTS"* ]]; then
      log "Setting codespaces secret ${CODESPACES_SECRET_NAME} from organization secret ${ORG_SECRET_NAME}..."
      
      # Get the secret value from organization secrets
      if [[ "${ORG_SECRET_NAME}" == "PROJECT_ID" && -n "${PROJECT_ID}" ]]; then
        if [[ "${PROJECT_ID}" != "USE_FROM_SECRET" ]]; then
          SECRET_VALUE="${PROJECT_ID}"
        else
          # Placeholder for when we can't directly access org secret values
          SECRET_VALUE="$(echo '${{ secrets.GCP_PROJECT_ID }}')"
        fi
      elif [[ "${ORG_SECRET_NAME}" == "PROJECT_NAME" && -n "${PROJECT_NAME}" ]]; then
        if [[ "${PROJECT_NAME}" != "USE_FROM_SECRET" ]]; then
          SECRET_VALUE="${PROJECT_NAME}"
        else
          # Placeholder for when we can't directly access org secret values
          SECRET_VALUE="$(echo '${{ secrets.GCP_PROJECT_NAME }}')"
        fi
      else
        # For key-related secrets, we have to use the placeholder syntax
        SECRET_VALUE="$(echo '${{ secrets.'${ORG_SECRET_NAME}' }}')"
      fi
      
      # URL-safe base64 encoding (using Python as it's likely available)
      ENCODED_SECRET=$(echo -n "${SECRET_VALUE}" | python3 -c "import base64, sys; print(base64.b64encode(sys.stdin.buffer.read()).decode().replace('+', '-').replace('/', '_').rstrip('='))")
      
      # Create/update secret in Codespaces
      RESPONSE=$(curl -s -X PUT \
        -H "${GITHUB_AUTH_HEADER}" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{\"encrypted_value\":\"${ENCODED_SECRET}\",\"key_id\":\"${ORG_CODESPACES_KEY_ID}\",\"visibility\":\"all\"}" \
        "${GITHUB_API_URL}/orgs/${GITHUB_ORG}/codespaces/secrets/${CODESPACES_SECRET_NAME}")
      
      if echo "${RESPONSE}" | grep -q "message"; then
        warn "Failed to update codespaces secret ${CODESPACES_SECRET_NAME}: $(echo ${RESPONSE} | jq -r '.message')"
      else
        log "Codespaces secret ${CODESPACES_SECRET_NAME} updated successfully."
      fi
    else
      warn "Skipping codespaces secret ${CODESPACES_SECRET_NAME} because source organization secret ${ORG_SECRET_NAME} does not exist."
    fi
  done
  
  log "GitHub Codespaces secrets have been updated from organization secrets."
}

# Create a documentation file for the GCP secrets setup
create_documentation() {
  step "Creating documentation for GCP secrets setup"
  
  DOC_FILE="GITHUB_GCP_SECRETS_SETUP.md"
  
  cat > "${DOC_FILE}" << EOL
# GitHub GCP Secrets Setup Documentation

This document describes the GitHub secrets setup for GCP authentication in both GitHub Actions and Codespaces environments.

## GitHub Organization Secrets

The following secrets are set at the GitHub organization level (${GITHUB_ORG}):

| Secret Name | Description | Used For |
|------------|-------------|----------|
| GCP_PROJECT_ID | The Google Cloud Project ID | Identifying the project in all GCP operations |
| GCP_PROJECT_NAME | The Google Cloud Project Name | Documentation and display purposes |
| GCP_PROJECT_ADMIN_KEY | Vertex AI admin service account key | Primary authentication for GitHub Actions workflows |
| GCP_VERTEX_AI_ADMIN_KEY | Same as PROJECT_ADMIN_KEY | Specific Vertex AI operations |
| GCP_SECRET_MANAGEMENT_KEY | Secret Management service account key | Managing GCP Secret Manager |
| GCP_GEMINI_API_KEY | Gemini API service account key | Authentication for Gemini API calls |
| GCP_GEMINI_CODE_ASSIST_KEY | Same as GEMINI_API_KEY | Specific for Gemini Code Assist |
| GCP_GEMINI_CLOUD_ASSIST_KEY | Same as GEMINI_API_KEY | Specific for Gemini Cloud Assist |

## GitHub Codespaces Environment Variables

The following environment variables are automatically set in GitHub Codespaces:

| Environment Variable | Source Secret | Description |
|---------------------|---------------|-------------|
| GCP_PROJECT_ID | GCP_PROJECT_ID | Project ID for GCP operations |
| GOOGLE_CLOUD_PROJECT | GCP_PROJECT_ID | Standard environment variable for GCP SDK |
| GCP_PROJECT_NAME | GCP_PROJECT_NAME | Project name for display purposes |
| GOOGLE_APPLICATION_CREDENTIALS | GCP_PROJECT_ADMIN_KEY | Standard GCP authentication credential path |
| VERTEX_AI_KEY | GCP_VERTEX_AI_ADMIN_KEY | Vertex AI authentication |
| GEMINI_API_KEY | GCP_GEMINI_API_KEY | Gemini API authentication |
| GEMINI_CODE_ASSIST_KEY | GCP_GEMINI_CODE_ASSIST_KEY | Gemini Code Assist authentication |
| GEMINI_CLOUD_ASSIST_KEY | GCP_GEMINI_CLOUD_ASSIST_KEY | Gemini Cloud Assist authentication |
| SECRET_MANAGER_KEY | GCP_SECRET_MANAGEMENT_KEY | Secret Manager authentication |

## GitHub Actions Authentication

The GitHub Actions workflows use the GCP_PROJECT_ADMIN_KEY for authentication:

\`\`\`yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    credentials_json: \${{ secrets.GCP_PROJECT_ADMIN_KEY }}
    create_credentials_file: true
\`\`\`

## Maintenance

To update these secrets, run:

1. For Vertex AI and Secret Management keys:
   \`\`\`bash
   ./create_service_accounts_and_update_secrets.sh
   \`\`\`

2. For Gemini-specific keys:
   \`\`\`bash
   ./setup_gemini_access.sh
   \`\`\`

3. To synchronize Codespaces environment variables:
   \`\`\`bash
   ./update_codespaces_secrets.sh
   \`\`\`
EOL

  log "Documentation file ${DOC_FILE} created."
}

# Main execution
main() {
  log "Starting GitHub Codespaces secrets update process"
  
  prompt_project_info
  update_codespaces_secrets
  create_documentation
  
  log "GitHub Codespaces secrets update completed successfully!"
  log ""
  log "GitHub Codespaces for organization ${GITHUB_ORG} now has the following environment variables set:"
  log "- GCP_PROJECT_ID"
  log "- GCP_PROJECT_NAME"
  log "- GOOGLE_CLOUD_PROJECT"
  log "- GOOGLE_APPLICATION_CREDENTIALS"
  log "- VERTEX_AI_KEY"
  log "- GEMINI_API_KEY"
  log "- GEMINI_CODE_ASSIST_KEY"
  log "- GEMINI_CLOUD_ASSIST_KEY"
  log "- SECRET_MANAGER_KEY"
  log ""
  log "Documentation has been created in: GITHUB_GCP_SECRETS_SETUP.md"
}

# Execute the script
main
