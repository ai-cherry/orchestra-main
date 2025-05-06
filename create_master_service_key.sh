#!/bin/bash
# Script to create a master service account key for GCP

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
: "${ENV:=dev}"

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

# Print header
log "INFO" "========================================================================="
log "INFO" "   MASTER SERVICE ACCOUNT KEY CREATOR   "
log "INFO" "========================================================================="

# Create service account if it doesn't exist
log "INFO" "Creating master service account..."
MASTER_SA_NAME="gcp-master-admin"
MASTER_SA_EMAIL="${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "${MASTER_SA_EMAIL}" --project="${GCP_PROJECT_ID}" &> /dev/null; then
  log "INFO" "Service account already exists. Skipping creation."
else
  gcloud iam service-accounts create "${MASTER_SA_NAME}" \
    --display-name="GCP Master Administrator Service Account" \
    --project="${GCP_PROJECT_ID}"
  log "SUCCESS" "Service account created successfully."
fi

# Assign comprehensive roles to the service account
log "INFO" "Assigning roles to ${MASTER_SA_EMAIL}..."

MASTER_ROLES=(
  "roles/owner"
  "roles/iam.serviceAccountAdmin"
  "roles/iam.serviceAccountKeyAdmin"
  "roles/secretmanager.admin"
  "roles/resourcemanager.projectIamAdmin"
  "roles/serviceusage.serviceUsageAdmin"
)

for role in "${MASTER_ROLES[@]}"; do
  log "INFO" "  - Assigning role: ${role}"
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${MASTER_SA_EMAIL}" \
    --role="${role}" \
    --quiet
done

log "SUCCESS" "Roles assigned successfully."

# Create and download service account key
log "INFO" "Creating and downloading key for ${MASTER_SA_EMAIL}..."
KEY_FILE=$(mktemp)

gcloud iam service-accounts keys create "${KEY_FILE}" \
  --iam-account="${MASTER_SA_EMAIL}" \
  --project="${GCP_PROJECT_ID}"

log "SUCCESS" "Key created and downloaded to temporary file"

# Read the key file content
MASTER_SA_KEY=$(cat "${KEY_FILE}")

# Base64 encode for GitHub secrets
MASTER_SA_KEY_BASE64=$(echo "${MASTER_SA_KEY}" | base64 -w 0)

# Save to a more secure temporary location
SECURE_TEMP_DIR=$(mktemp -d)
echo "${MASTER_SA_KEY}" > "${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key.json"
echo "${MASTER_SA_KEY_BASE64}" > "${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key-base64.txt"

log "INFO" "Key saved to ${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key.json"
log "INFO" "Base64 encoded key saved to ${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key-base64.txt"

# Store key in Secret Manager
log "INFO" "Storing ${MASTER_SA_NAME} key in Secret Manager"
if gcloud secrets describe "${MASTER_SA_NAME}-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
  gcloud secrets versions add "${MASTER_SA_NAME}-key" \
    --data-file="${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key.json" \
    --project="${GCP_PROJECT_ID}"
else
  gcloud secrets create "${MASTER_SA_NAME}-key" \
    --data-file="${SECURE_TEMP_DIR}/${MASTER_SA_NAME}-key.json" \
    --project="${GCP_PROJECT_ID}"
fi

# Securely remove the original temporary file
shred -u "${KEY_FILE}"

# Export the key as an environment variable
export GCP_MASTER_SERVICE_JSON="${MASTER_SA_KEY}"

log "SUCCESS" "Master service account key created successfully!"
log "INFO" "The key has been exported as GCP_MASTER_SERVICE_JSON environment variable."
log "INFO" "You can now run the orchestra_wif_master.sh script to set up Workload Identity Federation."
log "WARN" "IMPORTANT: Secure these keys and remove them from the filesystem after use!"

# Security reminder
log "WARN" "SECURITY WARNING:"
log "WARN" "1. The service account key created is highly privileged and should be protected."
log "WARN" "2. Consider setting up key rotation policies."
log "WARN" "3. Transition to Workload Identity Federation after initial setup."
log "WARN" "4. Delete keys from filesystem after use with: find /tmp -name '*-key*' -exec shred -u {} \;"