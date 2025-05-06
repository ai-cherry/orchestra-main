#!/bin/bash
# orchestra_wif_master.sh - Complete WIF setup using GCP_MASTER_SERVICE_JSON
# This script sets up Workload Identity Federation for GitHub Actions in the AI Orchestra project

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
: "${REGION:=us-west4}"
: "${POOL_ID:=github-actions-pool}"
: "${PROVIDER_ID:=github-actions-provider}"

# Service accounts to configure with specific roles
declare -A SERVICE_ACCOUNTS=(
  ["orchestrator-api"]="roles/run.admin roles/secretmanager.secretAccessor roles/firestore.user"
  ["phidata-agent-ui"]="roles/run.admin roles/secretmanager.secretAccessor"
  ["github-actions"]="roles/artifactregistry.writer roles/run.admin roles/secretmanager.secretAccessor roles/storage.admin"
  ["codespaces-dev"]="roles/viewer roles/secretmanager.secretAccessor roles/logging.viewer"
)

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
  
  # Set path to gcloud
  export PATH="/workspaces/orchestra-main/google-cloud-sdk/bin:$PATH"
  
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
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --project "${GCP_PROJECT_ID}"
  
  log "INFO" "APIs enabled successfully"
}

# Create Workload Identity Pool
create_identity_pool() {
  log "INFO" "Creating Workload Identity Pool..."
  if gcloud iam workload-identity-pools describe "${POOL_ID}" \
    --location="global" \
    --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Workload Identity Pool already exists"
  else
    gcloud iam workload-identity-pools create "${POOL_ID}" \
      --location="global" \
      --display-name="GitHub Actions Pool" \
      --description="Identity pool for GitHub Actions workflows" \
      --project="${GCP_PROJECT_ID}"
    
    log "INFO" "Workload Identity Pool created successfully"
  fi

  # Get the full pool name
  POOL_NAME=$(gcloud iam workload-identity-pools describe "${POOL_ID}" \
    --location="global" \
    --project="${GCP_PROJECT_ID}" \
    --format="value(name)")
  
  log "INFO" "Using Workload Identity Pool: ${POOL_NAME}"
}

# Create Workload Identity Provider
create_identity_provider() {
  log "INFO" "Creating Workload Identity Provider..."
  if gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" \
    --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Workload Identity Provider already exists"
  else
    gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
      --location="global" \
      --workload-identity-pool="${POOL_ID}" \
      --display-name="GitHub Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
      --issuer-uri="https://token.actions.githubusercontent.com" \
      --project="${GCP_PROJECT_ID}"
    
    log "INFO" "Workload Identity Provider created successfully"
  fi

  # Get the full provider name
  PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" \
    --project="${GCP_PROJECT_ID}" \
    --format="value(name)")
  
  # Save provider ID for GitHub secrets
  PROVIDER_VALUE="${PROVIDER_NAME}"
  echo "${PROVIDER_VALUE}" > "/tmp/wif_provider.txt"
  
  log "INFO" "Using Workload Identity Provider: ${PROVIDER_NAME}"
}

# Configure service accounts
configure_service_accounts() {
  log "INFO" "Configuring service accounts..."
  
  for SA_NAME in "${!SERVICE_ACCOUNTS[@]}"; do
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    ROLES=${SERVICE_ACCOUNTS[$SA_NAME]}
    
    log "INFO" "Processing service account: ${SA_EMAIL}"
    
    # Create service account if it doesn't exist
    if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
      log "INFO" "Service account ${SA_EMAIL} already exists"
    else
      log "INFO" "Creating service account ${SA_EMAIL}"
      gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="${SA_NAME} for WIF" \
        --project="${GCP_PROJECT_ID}"
    fi
    
    # Grant roles to the service account
    for ROLE in ${ROLES}; do
      log "INFO" "Granting ${ROLE} to ${SA_EMAIL}"
      gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${ROLE}"
    done
    
    # Configure workload identity federation for this service account
    log "INFO" "Configuring WIF binding for ${SA_EMAIL}"
    gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
      --role="roles/iam.workloadIdentityUser" \
      --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}" \
      --project="${GCP_PROJECT_ID}"
    
    # Save the primary service account email for GitHub secrets
    if [[ "${SA_NAME}" == "github-actions" ]]; then
      echo "${SA_EMAIL}" > "/tmp/service_account.txt"
    fi
  done
  
  log "INFO" "Service accounts configured successfully"
}

# Update GitHub secrets
update_github_secrets() {
  log "INFO" "Updating GitHub organization secrets..."
  
  if ! command -v gh &> /dev/null; then
    log "WARN" "GitHub CLI not found. Skipping GitHub secret updates"
    log "WARN" "You will need to manually set the following secrets in your GitHub organization:"
    log "WARN" "  - WIF_PROVIDER_ID: $(cat /tmp/wif_provider.txt 2>/dev/null || echo "Value not available")"
    log "WARN" "  - WIF_SERVICE_ACCOUNT: $(cat /tmp/service_account.txt 2>/dev/null || echo "Value not available")"
    return
  fi

  # Set the WIF_PROVIDER_ID secret
  PROVIDER_VALUE=$(cat /tmp/wif_provider.txt)
  log "INFO" "Setting WIF_PROVIDER_ID secret to: ${PROVIDER_VALUE}"
  gh secret set "WIF_PROVIDER_ID" --org "${GITHUB_ORG}" --body "${PROVIDER_VALUE}"

  # Set the WIF_SERVICE_ACCOUNT secret
  SA_EMAIL=$(cat /tmp/service_account.txt)
  log "INFO" "Setting WIF_SERVICE_ACCOUNT secret to: ${SA_EMAIL}"
  gh secret set "WIF_SERVICE_ACCOUNT" --org "${GITHUB_ORG}" --body "${SA_EMAIL}"

  # Set service account secrets for each service account
  for SA_NAME in "${!SERVICE_ACCOUNTS[@]}"; do
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    SECRET_NAME=$(echo "${SA_NAME}" | tr '-' '_' | tr '[:lower:]' '[:upper:]')_SERVICE_ACCOUNT
    
    log "INFO" "Setting ${SECRET_NAME} secret to: ${SA_EMAIL}"
    gh secret set "${SECRET_NAME}" --org "${GITHUB_ORG}" --body "${SA_EMAIL}"
  done
  
  log "INFO" "GitHub organization secrets updated successfully"
}

# Sync GitHub and GCP secrets
sync_secrets() {
  log "INFO" "Syncing GitHub organization secrets with GCP Secret Manager..."
  
  if [[ -f "./sync_github_gcp_secrets.sh" ]]; then
    chmod +x ./sync_github_gcp_secrets.sh
    ./sync_github_gcp_secrets.sh
  else
    log "WARN" "sync_github_gcp_secrets.sh not found. Skipping secret synchronization"
    log "WARN" "Please run sync_github_gcp_secrets.sh manually to synchronize secrets"
  fi
}

# Clean up temporary files
cleanup() {
  log "INFO" "Cleaning up temporary files..."
  rm -f /tmp/master-key.json
  rm -f /tmp/wif_provider.txt
  rm -f /tmp/service_account.txt
  
  log "INFO" "Cleanup complete"
}

# Main function
main() {
  log "INFO" "Starting Workload Identity Federation setup for AI Orchestra..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Authenticate with GitHub
  authenticate_github
  
  # Enable required APIs
  enable_apis
  
  # Create Workload Identity Pool
  create_identity_pool
  
  # Create Workload Identity Provider
  create_identity_provider
  
  # Configure service accounts
  configure_service_accounts
  
  # Update GitHub secrets
  update_github_secrets
  
  # Sync GitHub and GCP secrets
  sync_secrets
  
  # Clean up
  cleanup
  
  log "INFO" "Workload Identity Federation setup complete!"
  log "INFO" "Provider ID: $(cat /tmp/wif_provider.txt 2>/dev/null || echo "Not available")"
  log "INFO" "Service Account: $(cat /tmp/service_account.txt 2>/dev/null || echo "Not available")"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Run migrate_workflow_to_wif.sh to update your GitHub workflows"
  log "INFO" "2. Test a workflow to verify WIF authentication works"
  log "INFO" "3. Remove service account keys from GitHub secrets after confirming WIF works"
}

# Execute main function
main