#!/bin/bash
# Setup script for AI Orchestra memory infrastructure
# This script creates the necessary GCP resources for the memory system

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-west4"}
STORAGE_BUCKET=${STORAGE_BUCKET:-"${PROJECT_ID}-memory-embeddings"}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-"orchestra-memory-sa"}
SERVICE_ACCOUNT_DISPLAY_NAME=${SERVICE_ACCOUNT_DISPLAY_NAME:-"AI Orchestra Memory Service Account"}
TERRAFORM_DIR=${TERRAFORM_DIR:-"terraform"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print section header
section() {
  echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Print success message
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
error() {
  echo -e "${RED}✗ $1${NC}"
}

# Print info message
info() {
  echo -e "${YELLOW}➜ $1${NC}"
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
  section "Checking prerequisites"
  
  # Check if gcloud is installed
  if ! command_exists gcloud; then
    error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  success "gcloud CLI is installed"
  
  # Check if terraform is installed
  if ! command_exists terraform; then
    error "Terraform is not installed. Please install it from https://www.terraform.io/downloads.html"
    exit 1
  fi
  success "Terraform is installed"
  
  # Check if user is logged in to gcloud
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
    error "You are not logged in to gcloud. Please run 'gcloud auth login'"
    exit 1
  fi
  success "User is logged in to gcloud"
  
  # Check if project exists
  if ! gcloud projects describe "${PROJECT_ID}" >/dev/null 2>&1; then
    error "Project ${PROJECT_ID} does not exist or you don't have access to it"
    exit 1
  fi
  success "Project ${PROJECT_ID} exists and is accessible"
  
  # Set the project
  gcloud config set project "${PROJECT_ID}"
  success "Project set to ${PROJECT_ID}"
}

# Enable required APIs
enable_apis() {
  section "Enabling required APIs"
  
  # List of required APIs
  APIS=(
    "redis.googleapis.com"
    "firestore.googleapis.com"
    "aiplatform.googleapis.com"
    "secretmanager.googleapis.com"
    "storage.googleapis.com"
    "iam.googleapis.com"
  )
  
  for api in "${APIS[@]}"; do
    info "Enabling ${api}..."
    gcloud services enable "${api}" --project="${PROJECT_ID}"
    success "Enabled ${api}"
  done
}

# Create service account
create_service_account() {
  section "Creating service account"
  
  # Check if service account already exists
  if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    info "Service account ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com already exists"
  else
    # Create service account
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
      --display-name="${SERVICE_ACCOUNT_DISPLAY_NAME}" \
      --project="${PROJECT_ID}"
    success "Created service account ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
  fi
  
  # Grant roles to service account
  ROLES=(
    "roles/redis.editor"
    "roles/datastore.user"
    "roles/aiplatform.user"
    "roles/secretmanager.secretAccessor"
    "roles/storage.objectAdmin"
  )
  
  for role in "${ROLES[@]}"; do
    info "Granting ${role} to service account..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
      --role="${role}"
    success "Granted ${role} to service account"
  done
}

# Create storage bucket
create_storage_bucket() {
  section "Creating storage bucket"
  
  # Check if bucket already exists
  if gsutil ls -b "gs://${STORAGE_BUCKET}" >/dev/null 2>&1; then
    info "Bucket gs://${STORAGE_BUCKET} already exists"
  else
    # Create bucket
    gsutil mb -l "${REGION}" "gs://${STORAGE_BUCKET}"
    success "Created bucket gs://${STORAGE_BUCKET}"
  fi
  
  # Set bucket CORS configuration
  cat > /tmp/cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "PUT", "POST", "DELETE"],
    "responseHeader": ["Content-Type", "Content-Length", "Content-Encoding", "Content-Disposition"],
    "maxAgeSeconds": 3600
  }
]
EOF
  
  gsutil cors set /tmp/cors.json "gs://${STORAGE_BUCKET}"
  success "Set CORS configuration for bucket"
  
  # Grant service account access to bucket
  gsutil iam ch "serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com:objectAdmin" "gs://${STORAGE_BUCKET}"
  success "Granted service account access to bucket"
}

# Create Terraform variables file
create_terraform_variables() {
  section "Creating Terraform variables file"
  
  # Create terraform.tfvars file
  cat > "${TERRAFORM_DIR}/terraform.tfvars" << EOF
# Generated by setup_memory_infrastructure.sh

project_id = "${PROJECT_ID}"
region = "${REGION}"
storage_bucket = "${STORAGE_BUCKET}"
service_account_email = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
EOF
  
  success "Created ${TERRAFORM_DIR}/terraform.tfvars"
}

# Apply Terraform configuration
apply_terraform() {
  section "Applying Terraform configuration"
  
  # Initialize Terraform
  info "Initializing Terraform..."
  (cd "${TERRAFORM_DIR}" && terraform init)
  success "Terraform initialized"
  
  # Validate Terraform configuration
  info "Validating Terraform configuration..."
  (cd "${TERRAFORM_DIR}" && terraform validate)
  success "Terraform configuration is valid"
  
  # Plan Terraform changes
  info "Planning Terraform changes..."
  (cd "${TERRAFORM_DIR}" && terraform plan -out=tfplan)
  success "Terraform plan created"
  
  # Apply Terraform changes
  info "Applying Terraform changes..."
  (cd "${TERRAFORM_DIR}" && terraform apply tfplan)
  success "Terraform changes applied"
}

# Main function
main() {
  section "Setting up AI Orchestra memory infrastructure"
  
  check_prerequisites
  enable_apis
  create_service_account
  create_storage_bucket
  create_terraform_variables
  apply_terraform
  
  section "Setup complete"
  success "AI Orchestra memory infrastructure has been set up successfully"
  info "You can now use the memory system in your application"
}

# Run main function
main