#!/bin/bash
# Script to create comprehensive service account keys for Vertex AI and Gemini services
# and update GitHub organization-level secrets with the new keys and project information

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
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please ensure the Google Cloud SDK is installed and in your PATH"
    exit 1
  fi
  
  # Check for GitHub CLI
  GITHUB_CLI_AVAILABLE=false
  if command -v gh &> /dev/null; then
    GITHUB_CLI_AVAILABLE=true
    log "INFO" "GitHub CLI found. Will attempt to update GitHub secrets automatically."
    
    # Authenticate with GitHub CLI - only if GITHUB_TOKEN is provided
    if [ -n "${GITHUB_TOKEN:-}" ]; then
      log "INFO" "Authenticating with GitHub CLI..."
      echo "${GITHUB_TOKEN}" | gh auth login --with-token
      
      # Verify GitHub authentication
      if ! gh auth status &>/dev/null; then
        log "WARN" "Failed to authenticate with GitHub. GitHub secrets will not be updated automatically."
        GITHUB_CLI_AVAILABLE=false
      else
        log "SUCCESS" "Successfully authenticated with GitHub"
      fi
    else
      log "WARN" "No GITHUB_TOKEN provided. GitHub secrets will not be updated automatically."
      GITHUB_CLI_AVAILABLE=false
    fi
  else
    log "WARN" "GitHub CLI not found. GitHub secrets will not be updated automatically."
    log "WARN" "You will need to manually set the GitHub secrets."
  fi
  
  log "INFO" "All requirements satisfied"
}

# Run requirements check
check_requirements

# Check for required environment variables
if [[ -z "${GCP_MASTER_SERVICE_JSON}" && -z "${GCP_PROJECT_ADMIN_KEY}" && -z "${GCP_SECRET_MANAGEMENT_KEY}" ]]; then
  log "ERROR" "One of GCP_MASTER_SERVICE_JSON, GCP_PROJECT_ADMIN_KEY, or GCP_SECRET_MANAGEMENT_KEY environment variable is required"
  
  # Try to fetch secrets from GitHub if GitHub CLI is available
  if command -v gh &> /dev/null; then
    log "INFO" "Attempting to fetch secrets from GitHub..."
    
    GCP_PROJECT_ADMIN_KEY=$(gh secret get GCP_PROJECT_ADMIN_KEY --org "$GITHUB_ORG" 2>/dev/null)
    if [ -n "$GCP_PROJECT_ADMIN_KEY" ]; then
      log "SUCCESS" "Successfully fetched GCP_PROJECT_ADMIN_KEY from GitHub"
    fi
    
    GCP_SECRET_MANAGEMENT_KEY=$(gh secret get GCP_SECRET_MANAGEMENT_KEY --org "$GITHUB_ORG" 2>/dev/null)
    if [ -n "$GCP_SECRET_MANAGEMENT_KEY" ]; then
      log "SUCCESS" "Successfully fetched GCP_SECRET_MANAGEMENT_KEY from GitHub"
    fi
    
    # If still no keys, prompt for manual input
    if [[ -z "${GCP_MASTER_SERVICE_JSON}" && -z "${GCP_PROJECT_ADMIN_KEY}" && -z "${GCP_SECRET_MANAGEMENT_KEY}" ]]; then
      log "WARN" "No keys found in GitHub secrets"
      log "INFO" "Please provide a key file path manually"
      read -p "Path to service account key file: " KEY_FILE_PATH
      
      if [ -f "$KEY_FILE_PATH" ]; then
        GCP_MASTER_SERVICE_JSON=$(cat "$KEY_FILE_PATH")
        log "SUCCESS" "Successfully loaded key from $KEY_FILE_PATH"
      else
        log "ERROR" "File not found: $KEY_FILE_PATH"
        exit 1
      fi
    fi
  else
    log "ERROR" "GitHub CLI not available and no service account keys provided"
    log "INFO" "Please provide a key file path manually"
    read -p "Path to service account key file: " KEY_FILE_PATH
    
    if [ -f "$KEY_FILE_PATH" ]; then
      GCP_MASTER_SERVICE_JSON=$(cat "$KEY_FILE_PATH")
      log "SUCCESS" "Successfully loaded key from $KEY_FILE_PATH"
    else
      log "ERROR" "File not found: $KEY_FILE_PATH"
      exit 1
    fi
  fi
fi

# Service account names
VERTEX_SA_NAME="vertex-ai-admin"
GEMINI_API_SA_NAME="gemini-api-admin"
GEMINI_CODE_ASSIST_SA_NAME="gemini-code-assist-admin"
GEMINI_CLOUD_ASSIST_SA_NAME="gemini-cloud-assist-admin"
SECRET_MGMT_SA_NAME="secret-management-admin"

# Print header
log "INFO" "========================================================================="
log "INFO" "   COMPREHENSIVE VERTEX AI AND GEMINI SERVICE KEY CREATOR   "
log "INFO" "========================================================================="

# Function to check if gcloud is installed and authenticated
check_gcloud() {
  log "INFO" "Checking gcloud installation and authentication..."
  
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is not installed. Please install it first."
    exit 1
  fi
  
  # Authenticate with GCP using the provided key
  log "INFO" "Authenticating with GCP..."
  
  # Create a temporary file to store the service account key
  TEMP_KEY_FILE=$(mktemp)
  
  # Use the first available key
  if [ -n "${GCP_MASTER_SERVICE_JSON}" ]; then
    log "INFO" "Using GCP_MASTER_SERVICE_JSON for authentication"
    echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_KEY_FILE"
  elif [ -n "${GCP_PROJECT_ADMIN_KEY}" ]; then
    log "INFO" "Using GCP_PROJECT_ADMIN_KEY for authentication"
    echo "$GCP_PROJECT_ADMIN_KEY" > "$TEMP_KEY_FILE"
  elif [ -n "${GCP_SECRET_MANAGEMENT_KEY}" ]; then
    log "INFO" "Using GCP_SECRET_MANAGEMENT_KEY for authentication"
    echo "$GCP_SECRET_MANAGEMENT_KEY" > "$TEMP_KEY_FILE"
  else
    log "ERROR" "No service account key available for authentication"
    exit 1
  fi
  
  chmod 600 "$TEMP_KEY_FILE"
  gcloud auth activate-service-account --key-file="$TEMP_KEY_FILE"
  
  # Securely remove the temporary file
  shred -u "$TEMP_KEY_FILE"
  
  # Verify authentication
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log "ERROR" "Failed to authenticate with gcloud using the provided key."
    exit 1
  fi
  
  # Check if project exists and is accessible
  if ! gcloud projects describe "${GCP_PROJECT_ID}" &> /dev/null; then
    log "ERROR" "Project ${GCP_PROJECT_ID} does not exist or is not accessible."
    exit 1
  fi
  
  log "SUCCESS" "gcloud is properly configured."
}

# Function to create a service account if it doesn't exist
create_service_account() {
  local sa_name=$1
  local description=$2
  
  log "INFO" "Creating service account: ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com..."
  
  if gcloud iam service-accounts describe "${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    log "INFO" "Service account already exists. Skipping creation."
  else
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="${description}" \
      --project="${GCP_PROJECT_ID}"
    log "SUCCESS" "Service account created successfully."
  fi
}

# Function to assign roles to a service account
assign_roles() {
  local sa_name=$1
  local roles=("${@:2}")
  
  log "INFO" "Assigning roles to ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com..."
  
  for role in "${roles[@]}"; do
    log "INFO" "  - Assigning role: ${role}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
      --role="${role}" \
      --quiet
  done
  
  log "SUCCESS" "Roles assigned successfully."
}

# Function to create and download service account key
create_key() {
  local sa_name=$1
  local key_file=$(mktemp)

  log "INFO" "Creating and downloading key for ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com..."

  gcloud iam service-accounts keys create "${key_file}" \
    --iam-account="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${GCP_PROJECT_ID}"

  log "SUCCESS" "Key created and downloaded to temporary file"

  # Read the key file content
  SA_KEY=$(cat "${key_file}")

  # Base64 encode for GitHub secrets
  SA_KEY_BASE64=$(echo "${SA_KEY}" | base64 -w 0)

  # Save to a more secure temporary location
  SECURE_TEMP_DIR=$(mktemp -d)
  echo "${SA_KEY}" > "${SECURE_TEMP_DIR}/${sa_name}-key.json"
  echo "${SA_KEY_BASE64}" > "${SECURE_TEMP_DIR}/${sa_name}-key-base64.txt"
  
  log "INFO" "Key saved to ${SECURE_TEMP_DIR}/${sa_name}-key.json"
  log "INFO" "Base64 encoded key saved to ${SECURE_TEMP_DIR}/${sa_name}-key-base64.txt"

  # Store key in Secret Manager
  log "INFO" "Storing ${sa_name} key in Secret Manager"
  if gcloud secrets describe "${sa_name}-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "${sa_name}-key" \
      --data-file="${SECURE_TEMP_DIR}/${sa_name}-key.json" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "${sa_name}-key" \
      --data-file="${SECURE_TEMP_DIR}/${sa_name}-key.json" \
      --project="${GCP_PROJECT_ID}"
  fi

  # Securely remove the original temporary file
  shred -u "${key_file}"

  # Return the base64 encoded key
  echo "${SA_KEY_BASE64}"
}

# Function to update GitHub secrets
update_github_secret() {
  local secret_name=$1
  local secret_value=$2
  
  log "INFO" "Updating GitHub secret: ${secret_name}..."
  
  if [ "$GITHUB_CLI_AVAILABLE" = true ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    # Use GitHub CLI to set the secret
    if echo "${secret_value}" | gh secret set "${secret_name}" --org "${GITHUB_ORG}"; then
      log "SUCCESS" "Secret ${secret_name} updated successfully."
    else
      log "ERROR" "Failed to update secret ${secret_name}."
      log "INFO" "Please update it manually."
      manual_update_instructions "${secret_name}"
    fi
  else
    # Output instructions for manual update
    manual_update_instructions "${secret_name}"
  fi
}

# Function to display manual update instructions
manual_update_instructions() {
  local secret_name=$1
  
  log "INFO" "To update this secret manually:"
  log "INFO" "1. Go to ${GITHUB_ORG} organization settings"
  log "INFO" "2. Navigate to Secrets and variables -> Actions"
  log "INFO" "3. Add or update a secret with name: ${secret_name}"
  log "INFO" "4. Use the value from the secure temporary directory shown above"
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
  
  log "SUCCESS" "APIs enabled successfully"
}

# Main execution

# 1. Check requirements
check_requirements

# 2. Check gcloud setup
check_gcloud

# 3. Enable required APIs
enable_apis

# 4. Create and configure Vertex AI service account
create_service_account "${VERTEX_SA_NAME}" "Vertex AI Administrator Service Account"

# Assign comprehensive roles for Vertex AI
VERTEX_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/artifactregistry.admin"
  "roles/compute.admin"
  "roles/iam.serviceAccountUser"
  "roles/logging.admin"
  "roles/storage.admin"
  "roles/monitoring.admin"
  "roles/serviceusage.serviceUsageConsumer"
)
assign_roles "${VERTEX_SA_NAME}" "${VERTEX_ROLES[@]}"

# 5. Create and configure Gemini API service account
create_service_account "${GEMINI_API_SA_NAME}" "Gemini API Administrator Service Account"

# Assign comprehensive roles for Gemini API
GEMINI_API_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/serviceusage.serviceUsageConsumer"
  "roles/logging.admin"
  "roles/monitoring.admin"
)
assign_roles "${GEMINI_API_SA_NAME}" "${GEMINI_API_ROLES[@]}"

# 6. Create and configure Gemini Code Assist service account
create_service_account "${GEMINI_CODE_ASSIST_SA_NAME}" "Gemini Code Assist Administrator Service Account"

# Assign comprehensive roles for Gemini Code Assist
GEMINI_CODE_ASSIST_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/serviceusage.serviceUsageConsumer"
  "roles/logging.admin"
  "roles/monitoring.admin"
)
assign_roles "${GEMINI_CODE_ASSIST_SA_NAME}" "${GEMINI_CODE_ASSIST_ROLES[@]}"

# 7. Create and configure Gemini Cloud Assist service account
create_service_account "${GEMINI_CLOUD_ASSIST_SA_NAME}" "Gemini Cloud Assist Administrator Service Account"

# Assign comprehensive roles for Gemini Cloud Assist
GEMINI_CLOUD_ASSIST_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/serviceusage.serviceUsageConsumer"
  "roles/logging.admin"
  "roles/monitoring.admin"
)
assign_roles "${GEMINI_CLOUD_ASSIST_SA_NAME}" "${GEMINI_CLOUD_ASSIST_ROLES[@]}"

# 8. Create and configure Secret Management service account
create_service_account "${SECRET_MGMT_SA_NAME}" "Secret Management Service Account"

# Assign comprehensive roles for Secret Management
SECRET_MGMT_ROLES=(
  "roles/secretmanager.admin"
  "roles/secretmanager.secretAccessor"
  "roles/iam.serviceAccountUser"
  "roles/iam.serviceAccountKeyAdmin"
  "roles/iam.serviceAccountTokenCreator"
)
assign_roles "${SECRET_MGMT_SA_NAME}" "${SECRET_MGMT_ROLES[@]}"

# 9. Create service account keys
log "INFO" "Creating service account keys..."
VERTEX_SA_KEY=$(create_key "${VERTEX_SA_NAME}")
GEMINI_API_SA_KEY=$(create_key "${GEMINI_API_SA_NAME}")
GEMINI_CODE_ASSIST_SA_KEY=$(create_key "${GEMINI_CODE_ASSIST_SA_NAME}")
GEMINI_CLOUD_ASSIST_SA_KEY=$(create_key "${GEMINI_CLOUD_ASSIST_SA_NAME}")
SECRET_MGMT_SA_KEY=$(create_key "${SECRET_MGMT_SA_NAME}")

# 10. Save project ID for GitHub secrets
SECURE_TEMP_DIR=$(mktemp -d)
echo "${GCP_PROJECT_ID}" > "${SECURE_TEMP_DIR}/GCP_PROJECT_ID.txt"

# 11. Update GitHub secrets or output instructions
log "INFO" "========================================================================="
log "INFO" "   GITHUB SECRET UPDATE INSTRUCTIONS   "
log "INFO" "========================================================================="

update_github_secret "VERTEX_AI_FULL_ACCESS_KEY" "${VERTEX_SA_KEY}"
update_github_secret "GEMINI_API_FULL_ACCESS_KEY" "${GEMINI_API_SA_KEY}"
update_github_secret "GEMINI_CODE_ASSIST_FULL_ACCESS_KEY" "${GEMINI_CODE_ASSIST_SA_KEY}"
update_github_secret "GEMINI_CLOUD_ASSIST_FULL_ACCESS_KEY" "${GEMINI_CLOUD_ASSIST_SA_KEY}"
update_github_secret "GCP_SECRET_MANAGEMENT_KEY" "${SECRET_MGMT_SA_KEY}"
update_github_secret "GCP_PROJECT_ID" "${GCP_PROJECT_ID}"
update_github_secret "GCP_REGION" "${REGION}"

log "SUCCESS" "Service account keys created successfully!"
log "INFO" "Check the secure temporary directories for all generated keys and values."
log "WARN" "IMPORTANT: Secure these keys and remove them from the filesystem after use!"

# 12. Security reminder
log "WARN" "SECURITY WARNING:"
log "WARN" "1. The service account keys created are highly privileged and should be protected."
log "WARN" "2. Consider setting up key rotation policies."
log "WARN" "3. Transition to Workload Identity Federation after initial setup."
log "WARN" "4. Delete keys from filesystem after use with: find /tmp -name '*-key*' -exec shred -u {} \;"
log "WARN" "5. For maximum security, consider rotating these keys regularly and transitioning to Workload Identity Federation."

# 13. Update GitHub Codespaces environment variables
log "INFO" "To update GitHub Codespaces environment variables:"
log "INFO" "1. Go to ${GITHUB_ORG} organization settings"
log "INFO" "2. Navigate to Codespaces"
log "INFO" "3. Add or update the following environment variables:"
log "INFO" "   - GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
log "INFO" "   - GOOGLE_CLOUD_PROJECT: ${GCP_PROJECT_ID}"
log "INFO" "   - VERTEX_AI_KEY: Use the VERTEX_AI_FULL_ACCESS_KEY value"
log "INFO" "   - GEMINI_API_KEY: Use the GEMINI_API_FULL_ACCESS_KEY value"
log "INFO" "   - GEMINI_CODE_ASSIST_KEY: Use the GEMINI_CODE_ASSIST_FULL_ACCESS_KEY value"
log "INFO" "   - GEMINI_CLOUD_ASSIST_KEY: Use the GEMINI_CLOUD_ASSIST_FULL_ACCESS_KEY value"
log "INFO" "   - SECRET_MANAGER_KEY: Use the GCP_SECRET_MANAGEMENT_KEY value"
