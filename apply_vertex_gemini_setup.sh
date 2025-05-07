#!/bin/bash
# apply_vertex_gemini_setup.sh
# Script to apply Terraform configuration and set up GitHub secrets for Vertex AI and Gemini

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"
GITHUB_ORG="ai-cherry"
GITHUB_REPO="orchestra-main"
GITHUB_TOKEN="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"

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

# Authenticate with GCP using the project admin service account
authenticate_with_gcp() {
  log "INFO" "Authenticating with GCP using project admin service account key..."
  
  # Check if service-account-key.json exists
  if [ ! -f "service-account-key.json" ]; then
    log "ERROR" "service-account-key.json not found"
    exit 1
  fi
  
  # Authenticate with gcloud
  gcloud auth activate-service-account --key-file=service-account-key.json
  
  # Set the project
  gcloud config set project ${PROJECT_ID}
  
  log "SUCCESS" "Authenticated with GCP"
}

# Initialize and apply Terraform
apply_terraform() {
  log "INFO" "Initializing and applying Terraform configuration..."
  
  # Change to terraform directory
  cd terraform
  
  # Initialize Terraform
  log "INFO" "Initializing Terraform..."
  terraform init
  
  # Apply Terraform
  log "INFO" "Applying Terraform configuration..."
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
  if gcloud secrets describe "vertex-ai-key" --project=${PROJECT_ID} &>/dev/null; then
    log "INFO" "Updating secret vertex-ai-key..."
    gcloud secrets versions add "vertex-ai-key" \
      --data-file="vertex-ai-key.json" \
      --project=${PROJECT_ID}
  else
    log "INFO" "Creating secret vertex-ai-key..."
    gcloud secrets create "vertex-ai-key" \
      --data-file="vertex-ai-key.json" \
      --project=${PROJECT_ID}
  fi
  
  # Create secret for Gemini key
  if gcloud secrets describe "gemini-key" --project=${PROJECT_ID} &>/dev/null; then
    log "INFO" "Updating secret gemini-key..."
    gcloud secrets versions add "gemini-key" \
      --data-file="gemini-key.json" \
      --project=${PROJECT_ID}
  else
    log "INFO" "Creating secret gemini-key..."
    gcloud secrets create "gemini-key" \
      --data-file="gemini-key.json" \
      --project=${PROJECT_ID}
  fi
  
  log "SUCCESS" "Keys stored in Secret Manager"
}

# Store keys in GitHub secrets
store_keys_in_github_secrets() {
  log "INFO" "Storing keys in GitHub secrets..."
  
  # Authenticate with GitHub
  echo "${GITHUB_TOKEN}" | gh auth login --with-token
  
  # Store Vertex AI key
  log "INFO" "Storing Vertex AI key in GitHub secrets..."
  cat vertex-ai-key.json | gh secret set "VERTEX_SERVICE_ACCOUNT_KEY" --org "${GITHUB_ORG}" --body -
  
  # Store Gemini key
  log "INFO" "Storing Gemini key in GitHub secrets..."
  cat gemini-key.json | gh secret set "GEMINI_SERVICE_ACCOUNT_KEY" --org "${GITHUB_ORG}" --body -
  
  # Store Workload Identity Provider
  log "INFO" "Storing Workload Identity Provider in GitHub secrets..."
  WORKLOAD_IDENTITY_PROVIDER=$(terraform -chdir=terraform output -raw workload_identity_provider)
  echo "${WORKLOAD_IDENTITY_PROVIDER}" | gh secret set "WORKLOAD_IDENTITY_PROVIDER" --org "${GITHUB_ORG}" --body -
  
  log "SUCCESS" "Keys stored in GitHub secrets"
}

# Create GitHub Actions workflow
create_github_actions_workflow() {
  log "INFO" "Creating GitHub Actions workflow..."
  
  # Create .github/workflows directory if it doesn't exist
  mkdir -p .github/workflows
  
  # Create workflow file
  cat > .github/workflows/deploy-to-gcp.yml << EOF
name: Deploy to GCP

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.5.1
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: \${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: \${{ secrets.VERTEX_SERVICE_ACCOUNT_EMAIL }}
          project_id: ${PROJECT_ID}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy orchestra-api \\
            --source . \\
            --region us-central1 \\
            --platform managed \\
            --allow-unauthenticated
EOF
  
  log "SUCCESS" "GitHub Actions workflow created"
}

# Main function
main() {
  log "INFO" "Starting setup of Vertex AI and Gemini service accounts..."
  
  # Authenticate with GCP
  authenticate_with_gcp
  
  # Initialize and apply Terraform
  apply_terraform
  
  # Create service account keys
  create_service_account_keys
  
  # Store keys in Secret Manager
  store_keys_in_secret_manager
  
  # Store keys in GitHub secrets
  store_keys_in_github_secrets
  
  # Create GitHub Actions workflow
  create_github_actions_workflow
  
  log "SUCCESS" "Setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Created 'badass' Vertex AI service account with extensive permissions"
  log "INFO" "2. Created 'badass' Gemini service account with extensive permissions"
  log "INFO" "3. Set up Workload Identity Federation for GitHub Actions"
  log "INFO" "4. Created service account keys"
  log "INFO" "5. Stored keys in Secret Manager"
  log "INFO" "6. Stored keys in GitHub secrets"
  log "INFO" "7. Created GitHub Actions workflow"
  
  log "INFO" "You now have badass service accounts for Vertex AI and Gemini with extensive permissions!"
}

# Execute main function
main