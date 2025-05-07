you #!/bin/bash
# setup_workload_identity.sh
# Script to set up Workload Identity Federation for more secure authentication with GCP

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
GITHUB_REPO_OWNER="your-github-username"
GITHUB_REPO_NAME="orchestra-main"
SERVICE_ACCOUNT_NAME="orchestra-wif-sa"
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
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

# Function to check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Function to create a service account
create_service_account() {
  log "INFO" "Creating service account ${SERVICE_ACCOUNT_NAME}..."
  
  # Check if gcloud is installed
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI is not installed. Please install it first."
    exit 1
  fi
  
  # Check if service account already exists
  if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com &> /dev/null; then
    log "INFO" "Service account ${SERVICE_ACCOUNT_NAME} already exists."
  else
    # Create service account
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
      --display-name="Workload Identity Federation Service Account for GitHub Actions"
    
    log "SUCCESS" "Service account ${SERVICE_ACCOUNT_NAME} created successfully."
  fi
  
  # Grant necessary roles to the service account
  log "INFO" "Granting necessary roles to the service account..."
  
  # Cloud Run Admin role
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin"
  
  # Storage Admin role
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
  
  # Service Account User role
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
  
  log "SUCCESS" "Roles granted to service account successfully."
}

# Function to create a Workload Identity Pool
create_workload_identity_pool() {
  log "INFO" "Creating Workload Identity Pool ${POOL_NAME}..."
  
  # Check if pool already exists
  if gcloud iam workload-identity-pools describe ${POOL_NAME} --location=global &> /dev/null; then
    log "INFO" "Workload Identity Pool ${POOL_NAME} already exists."
  else
    # Create pool
    gcloud iam workload-identity-pools create ${POOL_NAME} \
      --location=global \
      --display-name="GitHub Actions Pool" \
      --description="Identity pool for GitHub Actions"
    
    log "SUCCESS" "Workload Identity Pool ${POOL_NAME} created successfully."
  fi
  
  # Get the full resource name of the pool
  POOL_ID=$(gcloud iam workload-identity-pools describe ${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  log "INFO" "Workload Identity Pool ID: ${POOL_ID}"
}

# Function to create a Workload Identity Provider
create_workload_identity_provider() {
  log "INFO" "Creating Workload Identity Provider ${PROVIDER_NAME}..."
  
  # Check if provider already exists
  if gcloud iam workload-identity-pools providers describe ${PROVIDER_NAME} \
    --workload-identity-pool=${POOL_NAME} \
    --location=global &> /dev/null; then
    log "INFO" "Workload Identity Provider ${PROVIDER_NAME} already exists."
  else
    # Create provider
    gcloud iam workload-identity-pools providers create-oidc ${PROVIDER_NAME} \
      --workload-identity-pool=${POOL_NAME} \
      --location=global \
      --display-name="GitHub Actions Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --issuer-uri="https://token.actions.githubusercontent.com"
    
    log "SUCCESS" "Workload Identity Provider ${PROVIDER_NAME} created successfully."
  fi
}

# Function to configure IAM policy binding
configure_iam_policy_binding() {
  log "INFO" "Configuring IAM policy binding..."
  
  # Get the full resource name of the pool
  POOL_ID=$(gcloud iam workload-identity-pools describe ${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  # Configure IAM policy binding
  gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}"
  
  log "SUCCESS" "IAM policy binding configured successfully."
}

# Function to create GitHub Actions workflow file
create_github_actions_workflow() {
  log "INFO" "Creating GitHub Actions workflow file..."
  
  # Create GitHub Actions directory
  mkdir -p .github/workflows
  
  # Get the full resource name of the pool
  POOL_ID=$(gcloud iam workload-identity-pools describe ${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  # Get the full resource name of the provider
  PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe ${PROVIDER_NAME} \
    --workload-identity-pool=${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  # Create GitHub Actions workflow file
  cat > .github/workflows/deploy-to-cloud-run-wif.yml << EOL
name: Deploy to Cloud Run with Workload Identity Federation

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      contents: 'read'
      id-token: 'write'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Google Auth
      id: auth
      uses: google-github-actions/auth@v1
      with:
        workload_identity_provider: '${PROVIDER_ID}'
        service_account: '${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com'
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
    
    - name: Build and Deploy to Cloud Run
      run: |
        gcloud builds submit --tag gcr.io/${PROJECT_ID}/orchestra-api
        gcloud run deploy orchestra-api \\
          --image gcr.io/${PROJECT_ID}/orchestra-api \\
          --platform managed \\
          --region ${REGION} \\
          --allow-unauthenticated
EOL
  
  log "SUCCESS" "GitHub Actions workflow file created successfully."
  log "INFO" "Workflow file: .github/workflows/deploy-to-cloud-run-wif.yml"
}

# Function to print setup information
print_setup_info() {
  log "INFO" "Workload Identity Federation setup information:"
  log "INFO" "Project ID: ${PROJECT_ID}"
  log "INFO" "Region: ${REGION}"
  log "INFO" "Service Account: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
  
  # Get the full resource name of the pool
  POOL_ID=$(gcloud iam workload-identity-pools describe ${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  # Get the full resource name of the provider
  PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe ${PROVIDER_NAME} \
    --workload-identity-pool=${POOL_NAME} \
    --location=global \
    --format="value(name)")
  
  log "INFO" "Workload Identity Pool ID: ${POOL_ID}"
  log "INFO" "Workload Identity Provider ID: ${PROVIDER_ID}"
  
  log "INFO" "To use Workload Identity Federation in GitHub Actions, add the following to your workflow file:"
  echo -e "${BLUE}
    - name: Google Auth
      id: auth
      uses: google-github-actions/auth@v1
      with:
        workload_identity_provider: '${PROVIDER_ID}'
        service_account: '${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com'
  ${NC}"
}

# Main function
main() {
  log "INFO" "Starting Workload Identity Federation setup..."
  
  # Check if gcloud is installed
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI is not installed. Please install it first."
    exit 1
  fi
  
  # Check if user is authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log "ERROR" "You are not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
  fi
  
  # Create service account
  create_service_account
  
  # Create Workload Identity Pool
  create_workload_identity_pool
  
  # Create Workload Identity Provider
  create_workload_identity_provider
  
  # Configure IAM policy binding
  configure_iam_policy_binding
  
  # Create GitHub Actions workflow file
  create_github_actions_workflow
  
  # Print setup information
  print_setup_info
  
  log "SUCCESS" "Workload Identity Federation setup completed successfully!"
}

# Run the main function
main