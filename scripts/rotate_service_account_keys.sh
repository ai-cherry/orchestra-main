#!/bin/bash
# rotate_service_account_keys.sh - Rotate service account keys for enhanced security

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
: "${KEY_ROTATION_PERIOD_DAYS:=90}"
: "${BACKUP_DIR:=./key_backups}"
: "${LOG_FILE:=./key_rotation.log}"

# Service accounts to rotate keys for
SERVICE_ACCOUNTS=(
  "vertex-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  "gemini-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
)

# Secret names in Secret Manager
SECRET_NAMES=(
  "vertex-power-key"
  "gemini-power-key"
)

# GitHub organization secrets
GITHUB_ORG_SECRETS=(
  "GCP_VERTEX_POWER_KEY"
  "GCP_GEMINI_POWER_KEY"
)

# Log function with timestamps
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  # Log to console
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
  
  # Log to file
  echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
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
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is required but not found"
    log "INFO" "Please install it: https://stedolan.github.io/jq/download/"
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
  
  # Create backup directory if it doesn't exist
  mkdir -p "${BACKUP_DIR}"
  
  # Create log file if it doesn't exist
  touch "${LOG_FILE}"
  
  log "SUCCESS" "All requirements satisfied"
}

# Authenticate with GCP
authenticate_gcp() {
  log "STEP" "Authenticating with GCP..."
  
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

# Check if key rotation is needed
check_key_rotation_needed() {
  local sa_email=$1
  local secret_name=$2
  
  log "INFO" "Checking if key rotation is needed for ${sa_email}..."
  
  # Get the current key from Secret Manager
  if ! gcloud secrets versions access latest --secret="${secret_name}" &>/dev/null; then
    log "WARN" "Secret ${secret_name} not found, key rotation is needed"
    return 0
  fi
  
  # Get the creation time of the latest key
  local key_json=$(gcloud secrets versions access latest --secret="${secret_name}")
  local key_id=$(echo "${key_json}" | jq -r '.private_key_id')
  
  # Get the key metadata
  local key_metadata=$(gcloud iam service-accounts keys list --iam-account="${sa_email}" --format=json | jq -r ".[] | select(.name | endswith(\"${key_id}\"))")
  
  if [ -z "${key_metadata}" ]; then
    log "WARN" "Key metadata not found, key rotation is needed"
    return 0
  fi
  
  # Get the creation time
  local creation_time=$(echo "${key_metadata}" | jq -r '.validAfterTime')
  local creation_date=$(date -d "${creation_time}" +%s)
  local current_date=$(date +%s)
  local days_diff=$(( (current_date - creation_date) / 86400 ))
  
  log "INFO" "Key for ${sa_email} is ${days_diff} days old"
  
  if [ ${days_diff} -ge ${KEY_ROTATION_PERIOD_DAYS} ]; then
    log "INFO" "Key rotation is needed for ${sa_email}"
    return 0
  else
    log "INFO" "Key rotation is not needed for ${sa_email}"
    return 1
  fi
}

# Rotate service account key
rotate_service_account_key() {
  local sa_email=$1
  local secret_name=$2
  local github_secret=$3
  
  log "STEP" "Rotating key for ${sa_email}..."
  
  # Create a temporary directory for the keys
  local temp_dir=$(mktemp -d)
  local new_key_file="${temp_dir}/new_key.json"
  local old_key_file="${temp_dir}/old_key.json"
  
  # Get the current key from Secret Manager
  if gcloud secrets versions access latest --secret="${secret_name}" &>/dev/null; then
    gcloud secrets versions access latest --secret="${secret_name}" > "${old_key_file}"
    local old_key_id=$(jq -r '.private_key_id' "${old_key_file}")
    log "INFO" "Retrieved current key with ID ${old_key_id}"
  else
    log "WARN" "No existing key found in Secret Manager"
  fi
  
  # Create a new key
  log "INFO" "Creating new key for ${sa_email}..."
  gcloud iam service-accounts keys create "${new_key_file}" \
    --iam-account="${sa_email}"
  
  local new_key_id=$(jq -r '.private_key_id' "${new_key_file}")
  log "SUCCESS" "Created new key with ID ${new_key_id}"
  
  # Backup the old key
  if [ -f "${old_key_file}" ]; then
    local backup_file="${BACKUP_DIR}/${sa_email//[@.]/_}_${old_key_id}.json"
    cp "${old_key_file}" "${backup_file}"
    log "INFO" "Backed up old key to ${backup_file}"
  fi
  
  # Update Secret Manager
  log "INFO" "Updating Secret Manager with new key..."
  if gcloud secrets describe "${secret_name}" &>/dev/null; then
    gcloud secrets versions add "${secret_name}" --data-file="${new_key_file}"
  else
    gcloud secrets create "${secret_name}" --data-file="${new_key_file}"
  fi
  log "SUCCESS" "Updated Secret Manager with new key"
  
  # Update GitHub organization secrets
  if [ -n "${GITHUB_TOKEN}" ] && command -v gh &> /dev/null; then
    log "INFO" "Updating GitHub organization secret ${github_secret}..."
    echo "${GITHUB_TOKEN}" | gh auth login --with-token
    cat "${new_key_file}" | gh secret set "${github_secret}" --org "ai-cherry"
    log "SUCCESS" "Updated GitHub organization secret ${github_secret}"
  fi
  
  # Delete the old key
  if [ -f "${old_key_file}" ]; then
    log "INFO" "Deleting old key with ID ${old_key_id}..."
    gcloud iam service-accounts keys delete "${old_key_id}" \
      --iam-account="${sa_email}" \
      --quiet
    log "SUCCESS" "Deleted old key with ID ${old_key_id}"
  fi
  
  # Clean up
  rm -rf "${temp_dir}"
  
  log "SUCCESS" "Key rotation completed for ${sa_email}"
}

# Main function
main() {
  log "INFO" "Starting service account key rotation..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Rotate keys for each service account
  for i in "${!SERVICE_ACCOUNTS[@]}"; do
    local sa_email="${SERVICE_ACCOUNTS[$i]}"
    local secret_name="${SECRET_NAMES[$i]}"
    local github_secret="${GITHUB_ORG_SECRETS[$i]}"
    
    if check_key_rotation_needed "${sa_email}" "${secret_name}"; then
      rotate_service_account_key "${sa_email}" "${secret_name}" "${github_secret}"
    fi
  done
  
  log "SUCCESS" "Service account key rotation completed successfully!"
}

# Execute main function
main