#!/bin/bash
# setup_secure_credentials.sh
#
# This script sets up the secure credential management system for AI Orchestra.
# It creates the necessary infrastructure, migrates existing credentials to Secret Manager,
# and configures Workload Identity Federation for GitHub Actions.

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"
REGION="us-central1"
GITHUB_ORG="ai-cherry"
GITHUB_REPO="orchestra-main"
ENV="dev"  # Change to "prod" for production

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Functions
log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
  exit 1
}

log_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

log_info() {
  echo -e "${BLUE}ℹ️ $1${NC}"
}

print_header() {
  echo -e "\n${BLUE}${BOLD}$1${NC}"
  echo -e "${BLUE}${BOLD}$(printf '=%.0s' $(seq 1 ${#1}))${NC}"
}

check_prerequisites() {
  print_header "Checking Prerequisites"
  
  # Check if gcloud is installed
  if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
  fi
  log_success "gcloud CLI is installed"
  
  # Check if terraform is installed
  if ! command -v terraform &> /dev/null; then
    log_error "Terraform is not installed. Please install it from https://www.terraform.io/downloads.html"
  fi
  log_success "Terraform is installed"
  
  # Check if authenticated with gcloud
  if ! gcloud auth list --filter=status=ACTIVE --format="value(account)" &> /dev/null; then
    log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
  fi
  log_success "Authenticated with gcloud"
  
  # Check if project exists
  if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    log_error "Project $PROJECT_ID does not exist or you don't have access to it"
  fi
  log_success "Project $PROJECT_ID exists and is accessible"
  
  # Check if APIs are enabled
  REQUIRED_APIS=("secretmanager.googleapis.com" "iam.googleapis.com" "cloudresourcemanager.googleapis.com" "run.googleapis.com")
  for api in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --enabled --filter="name:$api" --project="$PROJECT_ID" | grep -q "$api"; then
      log_info "Enabling $api..."
      gcloud services enable "$api" --project="$PROJECT_ID"
    fi
    log_success "$api is enabled"
  done
}

setup_service_account() {
  print_header "Setting Up Service Account"
  
  # Create service account for secret management if it doesn't exist
  if ! gcloud iam service-accounts describe "secret-management@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" &> /dev/null; then
    log_info "Creating service account for secret management..."
    gcloud iam service-accounts create "secret-management" \
      --display-name="Secret Management" \
      --description="Service account for managing secrets" \
      --project="$PROJECT_ID"
  else
    log_success "Service account secret-management already exists"
  fi
  
  # Grant necessary roles to the service account
  REQUIRED_ROLES=("roles/secretmanager.admin" "roles/iam.serviceAccountKeyAdmin")
  for role in "${REQUIRED_ROLES[@]}"; do
    log_info "Granting $role to service account..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:secret-management@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="$role"
  done
  
  # Create a key for the service account if it doesn't exist
  if [ ! -f "secret-management-key.json" ]; then
    log_info "Creating key for service account..."
    gcloud iam service-accounts keys create "secret-management-key.json" \
      --iam-account="secret-management@$PROJECT_ID.iam.gserviceaccount.com" \
      --project="$PROJECT_ID"
  else
    log_success "Service account key already exists"
  fi
  
  # Set the service account key as the active credentials
  export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/secret-management-key.json"
  log_success "Service account key set as active credentials"
}

setup_secret_manager() {
  print_header "Setting Up Secret Manager"
  
  # Create secrets for Redis
  log_info "Creating Redis secrets..."
  echo "localhost" | gcloud secrets create "redis-host-$ENV" --data-file=- --project="$PROJECT_ID" || \
    echo "localhost" | gcloud secrets versions add "redis-host-$ENV" --data-file=- --project="$PROJECT_ID"
  
  echo "orchestrapass" | gcloud secrets create "redis-password-$ENV" --data-file=- --project="$PROJECT_ID" || \
    echo "orchestrapass" | gcloud secrets versions add "redis-password-$ENV" --data-file=- --project="$PROJECT_ID"
  
  # Create secrets for Vertex AI
  log_info "Creating Vertex AI secrets..."
  echo "your-vertex-api-key" | gcloud secrets create "vertex-api-key-$ENV" --data-file=- --project="$PROJECT_ID" || \
    echo "your-vertex-api-key" | gcloud secrets versions add "vertex-api-key-$ENV" --data-file=- --project="$PROJECT_ID"
  
  # Store the service account key in Secret Manager
  log_info "Storing service account key in Secret Manager..."
  gcloud secrets create "secret-management-key" --data-file="secret-management-key.json" --project="$PROJECT_ID" || \
    gcloud secrets versions add "secret-management-key" --data-file="secret-management-key.json" --project="$PROJECT_ID"
  
  log_success "Secret Manager setup complete"
}

setup_workload_identity_federation() {
  print_header "Setting Up Workload Identity Federation"
  
  # Create a Workload Identity Pool if it doesn't exist
  if ! gcloud iam workload-identity-pools describe "github-pool" \
    --location="global" \
    --project="$PROJECT_ID" &> /dev/null; then
    log_info "Creating Workload Identity Pool..."
    gcloud iam workload-identity-pools create "github-pool" \
      --location="global" \
      --display-name="GitHub Actions Pool" \
      --description="Identity pool for GitHub Actions" \
      --project="$PROJECT_ID"
  else
    log_success "Workload Identity Pool already exists"
  fi
  
  # Get the Workload Identity Pool ID
  WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe "github-pool" \
    --location="global" \
    --format="value(name)" \
    --project="$PROJECT_ID")
  
  # Create a Workload Identity Provider if it doesn't exist
  if ! gcloud iam workload-identity-pools providers describe "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --project="$PROJECT_ID" &> /dev/null; then
    log_info "Creating Workload Identity Provider..."
    gcloud iam workload-identity-pools providers create-oidc "github-provider" \
      --location="global" \
      --workload-identity-pool="github-pool" \
      --display-name="GitHub Actions Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --issuer-uri="https://token.actions.githubusercontent.com" \
      --project="$PROJECT_ID"
  else
    log_success "Workload Identity Provider already exists"
  fi
  
  # Create a service account for GitHub Actions if it doesn't exist
  if ! gcloud iam service-accounts describe "github-actions@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" &> /dev/null; then
    log_info "Creating service account for GitHub Actions..."
    gcloud iam service-accounts create "github-actions" \
      --display-name="GitHub Actions" \
      --description="Service account for GitHub Actions" \
      --project="$PROJECT_ID"
  else
    log_success "Service account github-actions already exists"
  fi
  
  # Grant necessary roles to the service account
  REQUIRED_ROLES=("roles/run.admin" "roles/storage.admin" "roles/secretmanager.secretAccessor")
  for role in "${REQUIRED_ROLES[@]}"; do
    log_info "Granting $role to service account..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="$role"
  done
  
  # Allow the Workload Identity Pool to impersonate the service account
  log_info "Setting up service account impersonation..."
  gcloud iam service-accounts add-iam-policy-binding "github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}" \
    --project="$PROJECT_ID"
  
  # Get the Workload Identity Provider resource name
  WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --format="value(name)" \
    --project="$PROJECT_ID")
  
  log_success "Workload Identity Federation setup complete"
  log_info "Workload Identity Provider: $WORKLOAD_IDENTITY_PROVIDER"
  log_info "Service Account: github-actions@$PROJECT_ID.iam.gserviceaccount.com"
  
  # Output the values for GitHub Actions
  echo -e "\n${YELLOW}Add these secrets to your GitHub repository:${NC}"
  echo "WORKLOAD_IDENTITY_PROVIDER: $WORKLOAD_IDENTITY_PROVIDER"
  echo "SERVICE_ACCOUNT_EMAIL: github-actions@$PROJECT_ID.iam.gserviceaccount.com"
  echo "GCP_PROJECT_ID: $PROJECT_ID"
  echo "GCP_PROJECT_NUMBER: $PROJECT_NUMBER"
  echo "GCP_REGION: $REGION"
}

setup_terraform_backend() {
  print_header "Setting Up Terraform Backend"
  
  # Create a GCS bucket for Terraform state if it doesn't exist
  if ! gsutil ls -b "gs://$PROJECT_ID-terraform-state" &> /dev/null; then
    log_info "Creating GCS bucket for Terraform state..."
    gsutil mb -l "$REGION" "gs://$PROJECT_ID-terraform-state"
    
    # Enable versioning on the bucket
    gsutil versioning set on "gs://$PROJECT_ID-terraform-state"
  else
    log_success "GCS bucket for Terraform state already exists"
  fi
  
  log_success "Terraform backend setup complete"
}

main() {
  print_header "AI Orchestra Secure Credential Management Setup"
  
  # Check prerequisites
  check_prerequisites
  
  # Setup service account
  setup_service_account
  
  # Setup Secret Manager
  setup_secret_manager
  
  # Setup Workload Identity Federation
  setup_workload_identity_federation
  
  # Setup Terraform backend
  setup_terraform_backend
  
  log_success "Setup complete!"
  
  echo -e "\n${GREEN}${BOLD}Next Steps:${NC}"
  echo "1. Add the GitHub secrets mentioned above to your repository"
  echo "2. Update your .env file with the correct values"
  echo "3. Run Terraform to deploy the infrastructure"
  echo "4. Update your application code to use the new credential management system"
}

# Run the main function
main