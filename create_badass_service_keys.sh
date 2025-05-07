#!/bin/bash
# create_badass_service_keys.sh - Create powerful service account keys for Vertex AI and Gemini

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
PROJECT_NUMBER="525398941159"
REGION="us-central1"
GCP_USER_EMAIL="sccobyjava@cherry-ai.me"
VERTEX_SA_NAME="vertex-power-user"
GEMINI_SA_NAME="gemini-power-user"
SECRET_MANAGER_KEY="secret-management-key.json"
PROJECT_ADMIN_KEY="project-admin-key.json"

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
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GCP using Secret Manager key
authenticate_with_secret_manager() {
  log "INFO" "Authenticating with GCP using Secret Manager key..."
  
  # Authenticate with the service account key
  gcloud auth activate-service-account --key-file="${SECRET_MANAGER_KEY}" --impersonate-service-account="${GCP_USER_EMAIL}"
  
  # Set the project
  gcloud config set project "${PROJECT_ID}"
  
  log "SUCCESS" "Successfully authenticated with GCP using Secret Manager key (impersonating ${GCP_USER_EMAIL})"
}
# Authenticate with GCP using Project Admin key
authenticate_with_project_admin() {
  log "INFO" "Authenticating with GCP using Project Admin key..."
  
  # Authenticate with the service account key
  gcloud auth activate-service-account --key-file="${PROJECT_ADMIN_KEY}" --impersonate-service-account="${GCP_USER_EMAIL}"
  
  # Set the project
  gcloud config set project "${PROJECT_ID}"
  
  log "SUCCESS" "Successfully authenticated with GCP using Project Admin key (impersonating ${GCP_USER_EMAIL})"
}

# Create service account
create_service_account() {
  local sa_name=$1
  local sa_display_name=$2
  local sa_description=$3
  
  log "INFO" "Creating service account: ${sa_name}..."
  
  # Check if the service account already exists
  if gcloud iam service-accounts describe "${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" --project="${PROJECT_ID}" &>/dev/null; then
    log "INFO" "Service account ${sa_name} already exists"
  else
    # Create the service account
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="${sa_display_name}" \
      --description="${sa_description}" \
      --project="${PROJECT_ID}"
    
    log "SUCCESS" "Service account ${sa_name} created successfully"
  fi
}

# Grant role to service account
grant_role() {
  local sa_name=$1
  local role=$2
  
  log "INFO" "Granting role ${role} to service account ${sa_name}..."
  
  # Grant the role
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="${role}" \
    --condition=None
  
  log "SUCCESS" "Role ${role} granted to service account ${sa_name}"
}

# Create service account key
create_service_account_key() {
  local sa_name=$1
  local key_file=$2
  
  log "INFO" "Creating service account key for ${sa_name}..."
  
  # Create the key
  gcloud iam service-accounts keys create "${key_file}" \
    --iam-account="${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}"
  
  log "SUCCESS" "Service account key created successfully: ${key_file}"
}

# Store key in Secret Manager
store_key_in_secret_manager() {
  local secret_name=$1
  local key_file=$2
  
  log "INFO" "Storing key in Secret Manager: ${secret_name}..."
  
  # Check if the secret already exists
  if gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" &>/dev/null; then
    # Add a new version to the existing secret
    gcloud secrets versions add "${secret_name}" \
      --data-file="${key_file}" \
      --project="${PROJECT_ID}"
  else
    # Create a new secret
    gcloud secrets create "${secret_name}" \
      --data-file="${key_file}" \
      --project="${PROJECT_ID}"
  fi
  
  log "SUCCESS" "Key stored in Secret Manager: ${secret_name}"
}

# Create Vertex AI service account
create_vertex_service_account() {
  log "INFO" "Creating Vertex AI service account..."
  
  # Create the service account
  create_service_account "${VERTEX_SA_NAME}" "Vertex AI Power User" "Service account with powerful permissions for Vertex AI"
  
  # Grant roles
  grant_role "${VERTEX_SA_NAME}" "roles/aiplatform.admin"
  grant_role "${VERTEX_SA_NAME}" "roles/aiplatform.user"
  grant_role "${VERTEX_SA_NAME}" "roles/storage.admin"
  grant_role "${VERTEX_SA_NAME}" "roles/bigquery.admin"
  grant_role "${VERTEX_SA_NAME}" "roles/logging.admin"
  grant_role "${VERTEX_SA_NAME}" "roles/monitoring.admin"
  
  # Create a temporary directory for the key
  local temp_dir=$(mktemp -d)
  local key_file="${temp_dir}/vertex-key.json"
  
  # Create the key
  create_service_account_key "${VERTEX_SA_NAME}" "${key_file}"
  
  # Store the key in Secret Manager
  store_key_in_secret_manager "vertex-power-key" "${key_file}"
  
  # Clean up
  rm -f "${key_file}"
  rmdir "${temp_dir}"
  
  log "SUCCESS" "Vertex AI service account created successfully"
}

# Create Gemini service account
create_gemini_service_account() {
  log "INFO" "Creating Gemini service account..."
  
  # Create the service account
  create_service_account "${GEMINI_SA_NAME}" "Gemini Power User" "Service account with powerful permissions for Gemini"
  
  # Grant roles
  grant_role "${GEMINI_SA_NAME}" "roles/aiplatform.admin"
  grant_role "${GEMINI_SA_NAME}" "roles/aiplatform.user"
  grant_role "${GEMINI_SA_NAME}" "roles/storage.admin"
  grant_role "${GEMINI_SA_NAME}" "roles/logging.admin"
  grant_role "${GEMINI_SA_NAME}" "roles/monitoring.admin"
  
  # Create a temporary directory for the key
  local temp_dir=$(mktemp -d)
  local key_file="${temp_dir}/gemini-key.json"
  
  # Create the key
  create_service_account_key "${GEMINI_SA_NAME}" "${key_file}"
  
  # Store the key in Secret Manager
  store_key_in_secret_manager "gemini-power-key" "${key_file}"
  
  # Clean up
  rm -f "${key_file}"
  rmdir "${temp_dir}"
  
  log "SUCCESS" "Gemini service account created successfully"
}

# Update GitHub organization secrets
update_github_org_secrets() {
  log "INFO" "Updating GitHub organization secrets..."
  
  # Check if GitHub CLI is installed
  if ! command -v gh &> /dev/null; then
    log "WARN" "GitHub CLI not found, skipping GitHub secrets update"
    return
  fi
  
  # Check if GITHUB_TOKEN is set
  if [ -z "${GITHUB_TOKEN}" ]; then
    log "WARN" "GITHUB_TOKEN not set, skipping GitHub secrets update"
    return
  fi
  
  # Authenticate with GitHub
  echo "${GITHUB_TOKEN}" | gh auth login --with-token
  
  # Update GitHub organization secrets
  log "INFO" "Updating GCP_PROJECT_ID secret..."
  echo "${PROJECT_ID}" | gh secret set GCP_PROJECT_ID --org "ai-cherry"
  
  log "INFO" "Updating GCP_PROJECT_NUMBER secret..."
  echo "${PROJECT_NUMBER}" | gh secret set GCP_PROJECT_NUMBER --org "ai-cherry"
  
  log "INFO" "Updating GCP_REGION secret..."
  echo "${REGION}" | gh secret set GCP_REGION --org "ai-cherry"
  
  # Get the Vertex AI key from Secret Manager
  local vertex_key=$(gcloud secrets versions access latest --secret="vertex-power-key" --project="${PROJECT_ID}")
  log "INFO" "Updating GCP_VERTEX_POWER_KEY secret..."
  echo "${vertex_key}" | gh secret set GCP_VERTEX_POWER_KEY --org "ai-cherry"
  
  # Get the Gemini key from Secret Manager
  local gemini_key=$(gcloud secrets versions access latest --secret="gemini-power-key" --project="${PROJECT_ID}")
  log "INFO" "Updating GCP_GEMINI_POWER_KEY secret..."
  echo "${gemini_key}" | gh secret set GCP_GEMINI_POWER_KEY --org "ai-cherry"
  
  log "SUCCESS" "GitHub organization secrets updated successfully"
}

# Main function
main() {
  log "INFO" "Starting creation of powerful service account keys..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP using Project Admin key (has more permissions)
  authenticate_with_project_admin
  
  # Create Vertex AI service account
  create_vertex_service_account
  
  # Create Gemini service account
  create_gemini_service_account
  
  # Update GitHub organization secrets
  update_github_org_secrets
  
  log "SUCCESS" "Powerful service account keys created successfully!"
  log "INFO" "The keys have been stored in Secret Manager with the following names:"
  log "INFO" "- vertex-power-key"
  log "INFO" "- gemini-power-key"
  log "INFO" "The keys have also been added to GitHub organization secrets"
}

# Execute main function
main
