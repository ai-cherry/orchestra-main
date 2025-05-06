#!/bin/bash
# setup_gcp_infrastructure.sh - Script to set up GCP infrastructure and GitHub secrets
# This script automates the setup of GCP infrastructure and GitHub secrets for the AI Orchestra project

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
: "${ENV:=dev}"
: "${MASTER_SA_NAME:=gcp-master-admin}"
: "${TERRAFORM_STATE_BUCKET:=${GCP_PROJECT_ID}-terraform-state}"

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
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    log "ERROR" "GitHub CLI (gh) is required but not found"
    log "INFO" "Please install it: https://cli.github.com/manual/installation"
    exit 1
  fi
  
  # Check for GitHub PAT
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    log "INFO" "Please set it: export GITHUB_TOKEN=your_github_token"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
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
  
  log "SUCCESS" "Successfully authenticated with GitHub"
}

# Create GCP project if it doesn't exist
create_gcp_project() {
  log "INFO" "Checking if GCP project ${GCP_PROJECT_ID} exists..."
  
  if gcloud projects describe "${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "GCP project ${GCP_PROJECT_ID} already exists"
  else
    log "INFO" "Creating GCP project ${GCP_PROJECT_ID}..."
    gcloud projects create "${GCP_PROJECT_ID}" --name="AI Orchestra"
    log "SUCCESS" "GCP project ${GCP_PROJECT_ID} created successfully"
  fi
  
  # Set the project as the default
  gcloud config set project "${GCP_PROJECT_ID}"
  log "INFO" "Set ${GCP_PROJECT_ID} as the default project"
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
    run.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    --project "${GCP_PROJECT_ID}"
  
  log "SUCCESS" "APIs enabled successfully"
}

# Create master service account
create_master_service_account() {
  log "INFO" "Creating master service account..."
  
  # Create service account if it doesn't exist
  if gcloud iam service-accounts describe "${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Service account ${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com already exists"
  else
    gcloud iam service-accounts create "${MASTER_SA_NAME}" \
      --display-name="GCP Master Administrator" \
      --description="Service account with owner permissions for managing GCP infrastructure" \
      --project="${GCP_PROJECT_ID}"
    log "SUCCESS" "Service account ${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com created successfully"
  fi
  
  # Grant owner role to the service account
  log "INFO" "Granting owner role to ${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com..."
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/owner"
  
  log "SUCCESS" "Owner role granted to ${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
}

# Create master service account key
create_master_service_account_key() {
  log "INFO" "Creating master service account key..."
  
  # Create a temporary directory to store the key
  local temp_dir=$(mktemp -d)
  local key_file="${temp_dir}/master-key.json"
  
  # Create the key
  gcloud iam service-accounts keys create "${key_file}" \
    --iam-account="${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${GCP_PROJECT_ID}"
  
  log "SUCCESS" "Master service account key created at ${key_file}"
  
  # Store the key in Secret Manager
  log "INFO" "Storing master service account key in Secret Manager..."
  if gcloud secrets describe "master-service-account-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "master-service-account-key" \
      --data-file="${key_file}" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "master-service-account-key" \
      --data-file="${key_file}" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  log "SUCCESS" "Master service account key stored in Secret Manager"
  
  # Store the key in GitHub secrets
  log "INFO" "Storing master service account key in GitHub secrets..."
  cat "${key_file}" | gh secret set "GCP_MASTER_SERVICE_JSON" --org "${GITHUB_ORG}" --body -
  
  log "SUCCESS" "Master service account key stored in GitHub secrets"
  
  # Return the key file path
  echo "${key_file}"
}

# Create Terraform state bucket
create_terraform_state_bucket() {
  log "INFO" "Creating Terraform state bucket..."
  
  # Check if bucket exists
  if gcloud storage buckets describe "gs://${TERRAFORM_STATE_BUCKET}" &>/dev/null; then
    log "INFO" "Terraform state bucket gs://${TERRAFORM_STATE_BUCKET} already exists"
  else
    gcloud storage buckets create "gs://${TERRAFORM_STATE_BUCKET}" \
      --location="${REGION}" \
      --project="${GCP_PROJECT_ID}"
    log "SUCCESS" "Terraform state bucket gs://${TERRAFORM_STATE_BUCKET} created successfully"
  fi
  
  # Create or update Terraform backend configuration
  log "INFO" "Creating Terraform backend configuration..."
  
  mkdir -p terraform
  cat > terraform/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "${TERRAFORM_STATE_BUCKET}"
    prefix = "terraform/state"
  }
}
EOF
  
  log "SUCCESS" "Terraform backend configuration created at terraform/backend.tf"
}

# Store project configuration in GitHub secrets
store_project_config_in_github_secrets() {
  log "INFO" "Storing project configuration in GitHub secrets..."
  
  # Store GCP_PROJECT_ID
  gh secret set "GCP_PROJECT_ID" --org "${GITHUB_ORG}" --body "${GCP_PROJECT_ID}"
  
  # Store GCP_REGION
  gh secret set "GCP_REGION" --org "${GITHUB_ORG}" --body "${REGION}"
  
  log "SUCCESS" "Project configuration stored in GitHub secrets"
}

# Set up Workload Identity Federation
setup_workload_identity_federation() {
  log "INFO" "Setting up Workload Identity Federation..."
  
  # Run the orchestra_wif_master.sh script if it exists
  if [ -f "orchestra_wif_master.sh" ]; then
    log "INFO" "Running orchestra_wif_master.sh..."
    chmod +x orchestra_wif_master.sh
    
    # Export required environment variables
    export GCP_MASTER_SERVICE_JSON=$(cat "${1}")
    
    ./orchestra_wif_master.sh
  else
    log "ERROR" "orchestra_wif_master.sh not found"
    exit 1
  fi
  
  log "SUCCESS" "Workload Identity Federation set up successfully"
}

# Clean up temporary files
cleanup() {
  log "INFO" "Cleaning up temporary files..."
  
  # Find and securely delete all temporary key files
  find /tmp -name '*-key*' -exec shred -u {} \;
  
  log "SUCCESS" "Temporary files cleaned up"
}

# Main function
main() {
  log "INFO" "Starting GCP infrastructure setup..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Create GCP project if it doesn't exist
  create_gcp_project
  
  # Enable required APIs
  enable_apis
  
  # Create master service account
  create_master_service_account
  
  # Create master service account key
  local master_key_file=$(create_master_service_account_key)
  
  # Create Terraform state bucket
  create_terraform_state_bucket
  
  # Store project configuration in GitHub secrets
  store_project_config_in_github_secrets
  
  # Set up Workload Identity Federation
  setup_workload_identity_federation "${master_key_file}"
  
  # Clean up temporary files
  cleanup
  
  log "SUCCESS" "GCP infrastructure setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Created GCP project ${GCP_PROJECT_ID}"
  log "INFO" "2. Enabled required APIs"
  log "INFO" "3. Created master service account ${MASTER_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  log "INFO" "4. Created master service account key and stored it in Secret Manager and GitHub secrets"
  log "INFO" "5. Created Terraform state bucket gs://${TERRAFORM_STATE_BUCKET}"
  log "INFO" "6. Stored project configuration in GitHub secrets"
  log "INFO" "7. Set up Workload Identity Federation"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Push the changes to GitHub"
  log "INFO" "2. Run the GitHub Actions workflow to update the infrastructure"
  log "INFO" "3. Create a new Codespace or rebuild an existing one"
  log "INFO" "4. Run the test_gcp_integration.sh script to verify integration"
}

# Execute main function
main