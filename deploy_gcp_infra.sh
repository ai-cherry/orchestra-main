#!/bin/bash
# deploy_gcp_infra.sh
# Script to deploy infrastructure to GCP using real service account keys

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

# Create service account key file
create_service_account_key_file() {
  log "INFO" "Creating service account key file..."
  
  cat > project-admin-key.json << 'EOF'
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "216e545f19f380c72ad7eb704a15041621503f03",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDi3y+r4sY+2Jyj\ngdG/N5OrTNMKdhY2nndtxk4V4NVkRdSXKSGE3WEz6bLBaT0iVBXjDhuGyT1IzjiS\nCmkWjQ6CaGCwThjvHjkioHTIsgNO6/7FjCh0YRXJIz+gkY9O2P2UMKDMetlDz6la\nVdaFWHCro/ipoC9dZtiWxX7JoDw6+ZqoYct20qtrRDlh2trF+RT9QzxLJmeWoZxB\nvHU1oU1PsbGPDHyts/iXHqISyjEsUUtvOG/IsvMIWPVWvRCbnweQkktsATqzD7bH\nXZOj4cSqO2imAEPFkK/TZ+56JdjtHoZEaVyxzmXB4Pr9sde6KfuesdXjykufztMR\nwULU1B0fAgMBAAECggEASUsqVwD94+rN/ALiNMDrO5Gnsn8A4Sdj1PqWWnoW5nyq\n2CTpF8f/caqD3fk2T2NT6NUzbmGQI3fADepAFhF/CQFYj0zDwGiGs9mbsQTVjccv\nOTn1DdgZljAFi8XKwwHWNmxZXoYnr8EkaLNHiS/PwpvIJ2DBPI8P1PG76r6SBsjl\n7++ShV9r+m577erGvXUxk80dgYoHfBemwYBLSSm5LW0frSmEKHI7vBIT231YslTy\nYFODMOQQ0t+1MtX+7uNVyYOx+GdERkp9XfB3sgYVxZwdZ2pXha0pOZ2UieAm0Za6\nTNoUvhSYECXBfkMyXz89OaWI+4ycizvW9JziZeLk+QKBgQD5Znm9iYmdmvUYmI6T\nK7nBHDk3IXsJ+rwLOEDLHp0c1dhdgimgzFN81mKibDQ4jefRvTlDqSWbZ7Hn4YMF\nCTyZXgJKlU7A0qlufGWd3gfLGkwlDlzyi209mw7yE4W70sQpasea2e3cVWWYtxy9\nwSYQmxObgVZU5L7feVt1xmOIaQKBgQDo4BhN/6PzdnpyQfow4WLxFRCnjRnAZ4Ka\nLqHt8KB4L9K/3qjLFhJLNAUPcOL0C9K581CFfXqqN4gauKzGYa8id2RB9d8Q7LSE\nLNblKOMA3OoSGlWXDaWXLGLA9IsHyIgUqK6oRkoaW4a8XFN5ntgbJoEDpydfCXTs\nKOnAbIYIRwKBgQCB7U7y3RoiTz3siF2OcjMdVXTBMeIFeuhH+BBZQSOciBNl8494\nQ7oiyRUthK1X4SWp8KhKhW4gHc9i++rjzsIRLBaJgGs8rQKzmn7d1XO97X9JtsfZ\nW6WXeJY6qsz64nxrD0PZejselCaPfqWsfVk1QXTfiGvPYjPF/FUXcDkeMQKBgEOY\nYJWrYZyWxF4L9qJfmceetLHdzB7ELO2yIYCeewXH4+WbrOUeJ/s6Q0nDG615DRa6\noKHO1V85NUGEX2pKCnr3qttWkgQooRFIrqvf3Vxvw2WzzSpGZM1nrdaSZRTCSXWt\nrNzdYj8aWBauufAwgkwHNiWoTE5SwWSXT5pyJcmbAoGBALODSSlDnCtXqMry+lKx\nywyhRlYIk2QsmUjrJdYd74o6C8Q7D6o/p1Ah3uNl5fKvN+0QeNvpJB9yqiauS+w2\nlEMmVdcqYKwdmjkPxGiLKHhJcXiB62Nd5jUtVvGv9lz1c74bJdmhYjUOGuUtR5Ll\nxFFGN62B4+ed1wDppnemICJV\n-----END PRIVATE KEY-----\n",
  "client_email": "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "103717197419391442785",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/orchestra-project-admin-sa%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  
  log "SUCCESS" "Service account key file created"
}

# Authenticate with GCP
authenticate_with_gcp() {
  log "INFO" "Authenticating with GCP..."
  
  # Authenticate with gcloud
  gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=project-admin-key.json --project=${PROJECT_ID}
  
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
  
  # Create service account key file
  create_service_account_key_file
  
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