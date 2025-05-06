#!/bin/bash
# create_powerful_service_keys.sh - Create powerful service account keys for Vertex AI and Gemini

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
: "${REGION:=us-central1}"
: "${VERTEX_SA_NAME:=vertex-power-user}"
: "${GEMINI_SA_NAME:=gemini-power-user}"

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
  
  log "INFO" "All requirements satisfied"
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

# Create service account
create_service_account() {
  local sa_name=$1
  local sa_display_name=$2
  local sa_description=$3
  
  log "INFO" "Creating service account: ${sa_name}..."
  
  # Check if the service account already exists
  if gcloud iam service-accounts describe "${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Service account ${sa_name} already exists"
  else
    # Create the service account
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="${sa_display_name}" \
      --description="${sa_description}" \
      --project="${GCP_PROJECT_ID}"
    
    log "SUCCESS" "Service account ${sa_name} created successfully"
  fi
}

# Grant role to service account
grant_role() {
  local sa_name=$1
  local role=$2
  
  log "INFO" "Granting role ${role} to service account ${sa_name}..."
  
  # Grant the role
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
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
    --iam-account="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${GCP_PROJECT_ID}"
  
  log "SUCCESS" "Service account key created successfully: ${key_file}"
}

# Store key in Secret Manager
store_key_in_secret_manager() {
  local secret_name=$1
  local key_file=$2
  
  log "INFO" "Storing key in Secret Manager: ${secret_name}..."
  
  # Check if the secret already exists
  if gcloud secrets describe "${secret_name}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    # Add a new version to the existing secret
    gcloud secrets versions add "${secret_name}" \
      --data-file="${key_file}" \
      --project="${GCP_PROJECT_ID}"
  else
    # Create a new secret
    gcloud secrets create "${secret_name}" \
      --data-file="${key_file}" \
      --project="${GCP_PROJECT_ID}"
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

# Main function
main() {
  log "INFO" "Starting creation of powerful service account keys..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Create Vertex AI service account
  create_vertex_service_account
  
  # Create Gemini service account
  create_gemini_service_account
  
  log "SUCCESS" "Powerful service account keys created successfully!"
  log "INFO" "The keys have been stored in Secret Manager with the following names:"
  log "INFO" "- vertex-power-key"
  log "INFO" "- gemini-power-key"
}

# Execute main function
main