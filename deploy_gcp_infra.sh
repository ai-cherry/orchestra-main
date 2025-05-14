#!/bin/bash
# deploy_gcp_infra.sh
# Script to deploy infrastructure to GCP using a valid service account key file.
#
# Usage:
#   GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json ./deploy_gcp_infra.sh
# or
#   ./deploy_gcp_infra.sh /path/to/key.json
#
# The script requires a valid GCP service account key file with sufficient permissions.

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
KEY_FILE="${GOOGLE_APPLICATION_CREDENTIALS:-$1}"

# Log function
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

# (Removed insecure create_service_account_key_file function)

# Authenticate with GCP
authenticate_with_gcp() {
  log "INFO" "Authenticating with GCP..."

  if [[ -z "$KEY_FILE" ]]; then
    log "ERROR" "Service account key file not specified. Set GOOGLE_APPLICATION_CREDENTIALS or pass as argument."
    exit 1
  fi

  if [[ ! -f "$KEY_FILE" ]]; then
    log "ERROR" "Service account key file '$KEY_FILE' does not exist."
    exit 1
  fi

  # Extract client_email from key file
  CLIENT_EMAIL=$(python3 -c "import json; print(json.load(open('$KEY_FILE'))['client_email'])" 2>/dev/null)
  if [[ -z "$CLIENT_EMAIL" ]]; then
    log "ERROR" "Could not extract client_email from key file."
    exit 1
  fi

  # Authenticate with gcloud
  gcloud auth activate-service-account "$CLIENT_EMAIL" --key-file="$KEY_FILE" --project=${PROJECT_ID}

  # Set the project
  gcloud config set project ${PROJECT_ID}

  log "SUCCESS" "Authenticated with GCP"
}

# Enable required APIs
enable_apis() {
  log "INFO" "Enabling required APIs..."
  
  # List of APIs to enable
  apis=(
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "secretmanager.googleapis.com"
    "aiplatform.googleapis.com"
    "iamcredentials.googleapis.com"
  )
  
  # Enable each API
  for api in "${apis[@]}"; do
    log "INFO" "Enabling ${api}..."
    gcloud services enable ${api} --project=${PROJECT_ID}
  done
  
  log "SUCCESS" "Required APIs enabled"
}

# Create Terraform configuration
create_terraform_config() {
  log "INFO" "Creating Terraform configuration..."
  
  # Create terraform directory
  mkdir -p terraform
  
  # Create vertex_gemini_setup.tf
  cat > terraform/vertex_gemini_setup.tf << 'EOF'
# Terraform configuration for setting up "badass" Vertex AI and Gemini service accounts

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "cherry-ai-project"
  region  = "us-central1"
}

provider "google-beta" {
  project = "cherry-ai-project"
  region  = "us-central1"
}

# Create a "badass" Vertex AI service account with extensive permissions
resource "google_service_account" "vertex_ai_badass" {
  account_id   = "vertex-ai-badass"
  display_name = "Vertex AI Badass Service Account"
  description  = "Service account with extensive permissions for all Vertex AI operations"
}

# Grant comprehensive roles to the Vertex AI service account
resource "google_project_iam_member" "vertex_ai_admin" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_storage_admin" {
  project = "cherry-ai-project"
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

# Create a "badass" Gemini service account with extensive permissions
resource "google_service_account" "gemini_badass" {
  account_id   = "gemini-badass"
  display_name = "Gemini Badass Service Account"
  description  = "Service account with extensive permissions for all Gemini API operations"
}

# Grant comprehensive roles to the Gemini service account
resource "google_project_iam_member" "gemini_ai_platform_user" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

resource "google_project_iam_member" "gemini_service_usage" {
  project = "cherry-ai-project"
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

# Outputs
output "vertex_ai_service_account" {
  value = google_service_account.vertex_ai_badass.email
}

output "gemini_service_account" {
  value = google_service_account.gemini_badass.email
}
EOF
  
  log "SUCCESS" "Terraform configuration created"
}

# Apply Terraform
apply_terraform() {
  log "INFO" "Applying Terraform..."
  
  # Change to terraform directory
  cd terraform
  
  # Initialize Terraform
  terraform init
  
  # Apply Terraform
  terraform apply -auto-approve
  
  # Change back to root directory
  cd ..
  
  log "SUCCESS" "Terraform applied successfully"
}

# Create service account keys
create_service_account_keys() {
  log "INFO" "Creating service account keys..."
  
  # Get the Vertex AI service account email
  VERTEX_SA=$(terraform -chdir=terraform output -raw vertex_ai_service_account)
  
  # Get the Gemini service account email
  GEMINI_SA=$(terraform -chdir=terraform output -raw gemini_service_account)
  
  # Create key for Vertex AI service account
  log "INFO" "Creating key for Vertex AI service account..."
  gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=${VERTEX_SA}
  
  # Create key for Gemini service account
  log "INFO" "Creating key for Gemini service account..."
  gcloud iam service-accounts keys create gemini-key.json \
    --iam-account=${GEMINI_SA}
  
  log "SUCCESS" "Service account keys created"
}

# Store keys in Secret Manager
store_keys_in_secret_manager() {
  log "INFO" "Storing keys in Secret Manager..."
  
  # Create secret for Vertex AI key
  gcloud secrets create "vertex-ai-key" \
    --data-file="vertex-ai-key.json" \
    --project=${PROJECT_ID} || \
  gcloud secrets versions add "vertex-ai-key" \
    --data-file="vertex-ai-key.json" \
    --project=${PROJECT_ID}
  
  # Create secret for Gemini key
  gcloud secrets create "gemini-key" \
    --data-file="gemini-key.json" \
    --project=${PROJECT_ID} || \
  gcloud secrets versions add "gemini-key" \
    --data-file="gemini-key.json" \
    --project=${PROJECT_ID}
  
  log "SUCCESS" "Keys stored in Secret Manager"
}

# Main function
main() {
  log "INFO" "Starting GCP infrastructure deployment..."

  # Authenticate with GCP
  authenticate_with_gcp

  # Enable required APIs
  enable_apis

  # Create Terraform configuration
  create_terraform_config

  # Apply Terraform
  apply_terraform

  # Create service account keys
  create_service_account_keys

  # Store keys in Secret Manager
  store_keys_in_secret_manager

  log "SUCCESS" "GCP infrastructure deployment completed successfully!"
  log "INFO" "Vertex AI and Gemini service accounts have been created with badass permissions."
  log "INFO" "Service account keys have been stored in Secret Manager."
}

# Execute main function
main