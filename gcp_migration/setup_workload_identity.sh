#!/bin/bash
#
# Setup Workload Identity Federation for GitHub Actions
#
# This script sets up Workload Identity Federation (WIF) for GitHub Actions
# Using WIF eliminates the need for long-lived service account keys by allowing
# GitHub Actions to impersonate GCP service accounts securely.
#
# Usage: ./setup_workload_identity.sh [--project-id=<project-id>] [--repo=<owner/repo>]
#
# Author: Roo

set -e

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Log file
LOG_DIR="${SCRIPT_DIR}/migration_logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/wif_setup_$(date +%Y%m%d_%H%M%S).log"

# Default values
PROJECT_ID="cherry-ai-project"
REPO="owner/ai-orchestra" # Replace with your actual repo
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"
SERVICE_ACCOUNT="github-actions"
REGION="us-central1"

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --project-id=*)
    PROJECT_ID="${arg#*=}"
    shift
    ;;
    --repo=*)
    REPO="${arg#*=}"
    shift
    ;;
    *)
    # Unknown option
    echo -e "${RED}Unknown option: ${arg}${NC}"
    exit 1
    ;;
  esac
done

# Logging function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  case $level in
    INFO)
      echo -e "${GREEN}[INFO]${NC} ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    ERROR)
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    STEP)
      echo -e "${BLUE}[STEP]${NC} ${BOLD}${message}${NC}"
      ;;
    *)
      echo -e "${message}"
      ;;
  esac
  
  echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
}

# Check prerequisites
check_prerequisites() {
  log "STEP" "Checking prerequisites..."
  
  # Check if gcloud is installed
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud is not installed. Please install the Google Cloud SDK and try again."
    exit 1
  fi
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    log "ERROR" "jq is not installed. Please install jq and try again."
    exit 1
  fi
  
  
  # Check if logged into GCP
  if ! gcloud auth list 2>&1 | grep -q 'ACTIVE'; then
    log "ERROR" "Not authenticated with GCloud. Please run 'gcloud auth login' first."
    exit 1
  fi
  
  # Check if project exists and we have access
  if ! gcloud projects describe "${PROJECT_ID}" &> /dev/null; then
    log "ERROR" "Project ${PROJECT_ID} not found or you don't have access to it."
    exit 1
  fi
  
  # Set default project
  gcloud config set project "${PROJECT_ID}"
  
  log "INFO" "Prerequisites check passed."
}

# Create service account if it doesn't exist
create_service_account() {
  log "STEP" "Creating service account for GitHub Actions..."
  
  if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
      --display-name="GitHub Actions WIF" \
      --description="Service account for GitHub Actions Workload Identity Federation"
    log "INFO" "Service account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com created."
  else
    log "INFO" "Service account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com already exists."
  fi
  
  # Grant necessary roles to the service account
  log "INFO" "Granting necessary roles to service account..."
  
  # IAM roles required for GitHub Actions to deploy to Cloud Run, access secrets, etc.
  REQUIRED_ROLES=(
    "roles/run.admin"
    "roles/storage.admin" 
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/artifactregistry.admin"
  )
  
  for role in "${REQUIRED_ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
      --role="${role}"
    log "INFO" "Granted ${role} to service account."
  done
}

# Set up Workload Identity Federation
setup_workload_identity_federation() {
  log "STEP" "Setting up Workload Identity Federation..."
  
  # Enable required APIs
  log "INFO" "Enabling required APIs..."
  gcloud services enable iamcredentials.googleapis.com
  gcloud services enable iam.googleapis.com
  
  # Create the Workload Identity Pool if it doesn't exist
  if ! gcloud iam workload-identity-pools describe "${POOL_NAME}" \
      --location="global" &> /dev/null; then
    
    log "INFO" "Creating Workload Identity Pool: ${POOL_NAME}..."
    gcloud iam workload-identity-pools create "${POOL_NAME}" \
      --project="${PROJECT_ID}" \
      --location="global" \
      --display-name="GitHub Actions Pool"
  else
    log "INFO" "Workload Identity Pool ${POOL_NAME} already exists."
  fi
  
  # Get the full pool name
  POOL_ID=$(gcloud iam workload-identity-pools describe "${POOL_NAME}" \
    --location="global" \
    --format="value(name)")
  
  # Create the Workload Identity Provider if it doesn't exist
  if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
      --location="global" \
      --workload-identity-pool="${POOL_NAME}" &> /dev/null; then
    
    log "INFO" "Creating Workload Identity Provider: ${PROVIDER_NAME}..."
    gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
      --project="${PROJECT_ID}" \
      --location="global" \
      --workload-identity-pool="${POOL_NAME}" \
      --display-name="GitHub Actions Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --issuer-uri="https://token.actions.githubusercontent.com"
  else
    log "INFO" "Workload Identity Provider ${PROVIDER_NAME} already exists."
  fi
  
  # Get the provider full name
  PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --format="value(name)")
  
  # Allow the provider to impersonate the service account
  log "INFO" "Allowing the GitHub Actions workflow to impersonate the service account..."
  gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO}"
  
  log "INFO" "Workload Identity Federation setup completed."
}

# Generate GitHub Actions workflow with WIF configuration
generate_github_workflow() {
  log "STEP" "Generating GitHub Actions workflow template..."
  
  # Get the Workload Identity Provider
  PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --format="value(name)")
  
  # Create the .github/workflows directory if it doesn't exist
  mkdir -p "${PROJECT_ROOT}/.github/workflows"
  
  # Create a GitHub Actions workflow template
  WORKFLOW_FILE="${PROJECT_ROOT}/.github/workflows/deploy-with-wif.yml"
  
  cat > "${WORKFLOW_FILE}" << EOF
name: Deploy with Workload Identity Federation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: 'read'
  id-token: 'write'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: '${PROVIDER_ID}'
          service_account: '${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com'
          token_format: 'access_token'
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Google Container Registry
        uses: docker/login-action@v3
        with:
          registry: gcr.io
          username: _json_key
          password: \${{ steps.auth.outputs.access_token }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./services/admin-api
          push: true
          tags: gcr.io/${PROJECT_ID}/orchestra-admin-api:latest
      
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: orchestra-admin-api
          image: gcr.io/${PROJECT_ID}/orchestra-admin-api:latest
          region: ${REGION}
EOF
  
  log "INFO" "GitHub Actions workflow template generated at ${WORKFLOW_FILE}"
}

# Show information about the setup
show_info() {
  log "STEP" "Setup complete!"
  
  # Get the Workload Identity Provider
  PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --format="value(name)")
  
  cat << EOF

${GREEN}${BOLD}Workload Identity Federation Setup Complete!${NC}

${BLUE}Summary:${NC}
- Project ID: ${PROJECT_ID}
- Repository: ${REPO}
- Service Account: ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
- Workload Identity Pool: ${POOL_NAME}
- Workload Identity Provider: ${PROVIDER_NAME}

${BLUE}To use in GitHub Actions workflows:${NC}

\`\`\`yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: '${PROVIDER_ID}'
    service_account: '${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com'
\`\`\`

A GitHub Actions workflow template has been generated at:
${WORKFLOW_FILE}

${YELLOW}Note:${NC} Make sure to set the GitHub repository to match '${REPO}'
and configure the required GitHub repository permissions for Actions.

${GREEN}Documentation:${NC}
https://github.com/google-github-actions/auth

EOF
}

# Main execution
main() {
  echo -e "${BOLD}${BLUE}GitHub Actions Workload Identity Federation Setup${NC}"
  echo -e "${BLUE}============================================${NC}"
  
  log "INFO" "Starting setup for project ${PROJECT_ID} and repository ${REPO}..."
  log "INFO" "Log file: ${LOG_FILE}"
  
  # Execute steps
  check_prerequisites
  create_service_account
  setup_workload_identity_federation
  generate_github_workflow
  show_info
}

# Execute main function
main