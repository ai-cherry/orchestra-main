#!/bin/bash
# update_gcp_infrastructure.sh - Comprehensive script to update GCP infrastructure using GCP_MASTER_SERVICE_JSON
# This script updates everything in GCP and GitHub for the AI Orchestra project

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
    log "INFO" "Installing Google Cloud SDK..."
    
    # Install Google Cloud SDK
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-465.0.0-linux-x86_64.tar.gz
    tar -xf google-cloud-cli-465.0.0-linux-x86_64.tar.gz
    ./google-cloud-sdk/install.sh --quiet
    source ./google-cloud-sdk/path.bash.inc
    
    # Verify installation
    if ! command -v gcloud &> /dev/null; then
      log "ERROR" "Failed to install Google Cloud SDK"
      exit 1
    fi
    
    log "SUCCESS" "Google Cloud SDK installed successfully"
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
  
  # Check for GCP_MASTER_SERVICE_JSON
  if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is required"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GCP using the master service account key
authenticate_gcp() {
  log "INFO" "Authenticating with GCP using GCP_MASTER_SERVICE_JSON..."
  
  # Create a temporary file to store the service account key
  TEMP_KEY_FILE=$(mktemp)
  echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_KEY_FILE"
  chmod 600 "$TEMP_KEY_FILE"
  
  # Authenticate with gcloud
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
    --project "${GCP_PROJECT_ID}"
  
  log "SUCCESS" "APIs enabled successfully"
}

# Create service accounts and keys
create_service_accounts() {
  log "INFO" "Creating service accounts and keys..."
  
  # Run the create_badass_service_keys.sh script
  if [ -f "create_badass_service_keys.sh" ]; then
    log "INFO" "Running create_badass_service_keys.sh..."
    chmod +x create_badass_service_keys.sh
    ./create_badass_service_keys.sh
  else
    log "ERROR" "create_badass_service_keys.sh not found"
    exit 1
  fi
  
  log "SUCCESS" "Service accounts and keys created successfully"
}

# Update GitHub Codespaces secrets
update_codespaces_secrets() {
  log "INFO" "Updating GitHub Codespaces secrets..."
  
  # Run the update_codespaces_secrets.sh script
  if [ -f "scripts/update_codespaces_secrets.sh" ]; then
    log "INFO" "Running update_codespaces_secrets.sh..."
    chmod +x scripts/update_codespaces_secrets.sh
    ./scripts/update_codespaces_secrets.sh
  else
    log "ERROR" "scripts/update_codespaces_secrets.sh not found"
    exit 1
  fi
  
  log "SUCCESS" "GitHub Codespaces secrets updated successfully"
}

# Set up Workload Identity Federation
setup_workload_identity_federation() {
  log "INFO" "Setting up Workload Identity Federation..."
  
  # Run the orchestra_wif_master.sh script
  if [ -f "orchestra_wif_master.sh" ]; then
    log "INFO" "Running orchestra_wif_master.sh..."
    chmod +x orchestra_wif_master.sh
    ./orchestra_wif_master.sh
  else
    log "ERROR" "orchestra_wif_master.sh not found"
    exit 1
  fi
  
  log "SUCCESS" "Workload Identity Federation set up successfully"
}

# Test GCP integration
test_gcp_integration() {
  log "INFO" "Testing GCP integration..."
  
  # Run the test_gcp_integration.sh script
  if [ -f "scripts/test_gcp_integration.sh" ]; then
    log "INFO" "Running test_gcp_integration.sh..."
    chmod +x scripts/test_gcp_integration.sh
    ./scripts/test_gcp_integration.sh
  else
    log "ERROR" "scripts/test_gcp_integration.sh not found"
    exit 1
  fi
  
  log "SUCCESS" "GCP integration tests completed"
}

# Update Terraform state
update_terraform_state() {
  log "INFO" "Updating Terraform state..."
  
  # Check if Terraform directory exists
  if [ ! -d "terraform" ]; then
    log "ERROR" "terraform directory not found"
    exit 1
  fi
  
  # Initialize Terraform
  cd terraform
  terraform init
  
  # Apply Terraform changes
  terraform apply -auto-approve -var="project_id=${GCP_PROJECT_ID}" -var="region=${REGION}" -var="env=${ENV}"
  
  cd ..
  
  log "SUCCESS" "Terraform state updated successfully"
}

# Main function
main() {
  log "INFO" "Starting comprehensive GCP infrastructure update..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Enable required APIs
  enable_apis
  
  # Create service accounts and keys
  create_service_accounts
  
  # Update GitHub Codespaces secrets
  update_codespaces_secrets
  
  # Set up Workload Identity Federation
  setup_workload_identity_federation
  
  # Test GCP integration
  test_gcp_integration
  
  # Update Terraform state
  update_terraform_state
  
  log "SUCCESS" "GCP infrastructure update completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Authenticated with GCP using GCP_MASTER_SERVICE_JSON"
  log "INFO" "2. Enabled required GCP APIs"
  log "INFO" "3. Created service accounts and keys for Vertex AI and Gemini services"
  log "INFO" "4. Updated GitHub organization secrets with the new keys"
  log "INFO" "5. Updated GitHub Codespaces secrets with the new keys"
  log "INFO" "6. Set up Workload Identity Federation for GitHub Actions"
  log "INFO" "7. Tested the integration between GitHub, Codespaces, and GCP"
  log "INFO" "8. Updated Terraform state"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Commit and push the changes to your repository"
  log "INFO" "2. Create a new Codespace or rebuild an existing one"
  log "INFO" "3. Verify that the Codespace has access to GCP resources"
}

# Execute main function
main