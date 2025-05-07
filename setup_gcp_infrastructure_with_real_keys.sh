#!/bin/bash
# setup_gcp_infrastructure_with_real_keys.sh
# Script to set up GCP infrastructure using existing service account keys

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
REGION="us-central1"
GITHUB_ORG="ai-cherry"
GITHUB_REPO="orchestra-main"
GCP_USER_EMAIL="scoobyjava@cherry-ai.me"
GCP_BACKUP_EMAIL="musilllynn@gmail.com"
GITHUB_TOKEN="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"

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
# Create service account key files
create_service_account_key_files() {
  log "INFO" "Creating service account key files..."
  
  # Create secret-management-key.json if it doesn't exist
  if [ ! -f "secret-management-key.json" ]; then
    log "INFO" "Creating secret-management-key.json..."
    cat > secret-management-key.json << 'EOF'
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "c85ef791f1f460f6353748c02b781e34f6ac37f6",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQD2CQP78+4X/yIm\ncM9+RfnZm82KRFTVBWvGQ1EP/uZv8HBF1E6bAR1JCjRQY+Z5KrD//SlSYBxj5D87\nOfK4U83yfvukCXGBy4TT0h0WEDOjwE5GLs7e0bzd3bM5RbC2FWpMpcIjj2pN76hk\n7Men5KCHFPbZAIumW6gXiEyzpp9N4613dGt0878IpCHOeEz4ywo6vk4/6iGyR/nW\n1gk7TttkfXF6pZWaHAFBTRAgbHyyTtRvtGwjRRKCBm3sIPAyFVLLwte7697FX7rY\nu1/X5jcahNzB3xuTbOH9FyEArNV5FxfpeDMnAjBo1f/mGJBKgldObLtqnwS6VHkC\nnptBomi1AgMBAAECggEANr5sTMYqstuxx1BgFtZuoMEGU67fGlP9tkx5r7+1mfAr\npxn1kI9Hqx4SZFXKLSk234q+xEW+42oguKas7180SrH+/3GbeDgm2rPchXF+7/9k\n20BkhtcvuUUwcPyk9Grg72ONhjiNvIAoHabCyQR5xHzBbSjuKcqopO3OtUWMmjlw\nRrM0WZsN99Oc9qiZ6pP8aghdgMdCJ4W+LOZ91xUMoB6Eq2clpLeEP0sIQDkumWgj\nIGVvQRmy6oRhaMX79iW9T/hthZAkhnPEF5uvbVuzMw51tLYEhZNIYCioiBEbvxtg\nFll8KSIQlb39RP/hEstYGRoGNVwOSmQdbMvLgSIHoQKBgQD/YkPcuNIDK7OrB7cU\ncQJpj/6IVUstv5hSO0NxRF8337xzdW4iXAqSQNpAxhX4tSPF2iSZC8LxxczOXd11\nnk9EJr/mUtlrla+6TPPIZBKUMIZ6DJ1jWfsPvbL7MxO0abMbq0bXQ6noXfUVNxbU\n5dS6E207+6NSPPBX4AZkIzC2FQKBgQD2oPn1c5te70Lz3S0vtt+3vTVTIHI2s9xj\nJI00Rzy/fq1XrZvQjYR6+34uSx0x/5Yyueja6GhRBKL+QtMfkRao9psMli7C3FQV\nrScAUMvzTiv/yb6bIzWh/0KRux5SgYxMXxl4UTio8+bCFiXLVuhCsV5smBJhfB/Y\nhtrnWhswIQKBgQC++E1EzVQGGPTmjQNjnsouBAZTDm0ETcRqoXRiS71kO8NhF0v/\nF5K0IRjT3QxrCZExj1lUtM3XG5F2NAy5umMN1GglpIh/AdUBXC/kBqk59TtqIurC\nc3PhJnqji2NNwsizhRWZPTjd0PzHG4XQN/kmGAbUFuzfP0B+hcBhu0rerQKBgQCc\n5io+8c4tZi+E7veZPFE1FiT/fkvK6z/QvucqFAvck515gxP2aKGYj7hlgRnQvhXy\nrX0rDuGWcUm0UhT4JxhwY3qeVkjnZL4FkEOYms41Ok0ZjGI7Vfn/1mGmTpFq0cnM\nqE+O0LUoHwp1/RsMMnzOOQKmOVSwOgQUfy5yMkvLoQKBgQC1goo89ddrmNw789Rt\nTDw1ddLgIbaehmG29KVtCgwdPRB8z11mv3TUJqrwhwos3Q4VNlVaQ/UJh/cAIwvO\nE0ZkFTxY8vhw2NThfRECUa8+oqHeamOTWO5uBmWVU1K0s/0eNqIQ2J6myQDaLM9M\nZbqmklkysyPgJUHYDCV8lkugaA==\n-----END PRIVATE KEY-----\n",
  "client_email": "secret-management@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "106306054779443659925",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/secret-management%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  fi
  
  # Create project-admin-key.json if it doesn't exist
  if [ ! -f "project-admin-key.json" ]; then
    log "INFO" "Creating project-admin-key.json..."
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
  fi
  
  log "SUCCESS" "Service account key files created"
}

# Authenticate with GCP using service account key
authenticate_with_gcp() {
  log "INFO" "Authenticating with GCP using project admin service account key..."
  
  # Authenticate with gcloud using the project admin service account
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
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "aiplatform.googleapis.com"
    "compute.googleapis.com"
    "storage.googleapis.com"
    "iamcredentials.googleapis.com"
    "cloudbuild.googleapis.com"
    "cloudfunctions.googleapis.com"
    "generativelanguage.googleapis.com"
  )
  
  # Enable each API
  for api in "${apis[@]}"; do
    log "INFO" "Enabling ${api}..."
    gcloud services enable ${api} --project=${PROJECT_ID}
  done
  
  log "SUCCESS" "Required APIs enabled"
}
# Create Terraform state bucket
create_terraform_state_bucket() {
  log "INFO" "Creating Terraform state bucket..."
  
  # Bucket name
  BUCKET_NAME="${PROJECT_ID}-terraform-state"
  
  # Check if bucket exists
  if gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
    log "INFO" "Terraform state bucket gs://${BUCKET_NAME} already exists"
  else
    log "INFO" "Creating bucket gs://${BUCKET_NAME}..."
    gcloud storage buckets create "gs://${BUCKET_NAME}" --location=${REGION} --project=${PROJECT_ID}
  fi
  
  log "SUCCESS" "Terraform state bucket created/verified"
}

# Set up Terraform
setup_terraform() {
  log "INFO" "Setting up Terraform..."
  
  # Create terraform directory if it doesn't exist
  mkdir -p terraform
  
  # Create backend.tf
  cat > terraform/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "${PROJECT_ID}-terraform-state"
    prefix = "terraform/state"
  }
}
EOF
  
  # Create provider.tf
  cat > terraform/provider.tf << EOF
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
EOF
  
  # Create variables.tf
  cat > terraform/variables.tf << EOF
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "${PROJECT_ID}"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "${REGION}"
}

variable "env" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
EOF
  
  # Create main.tf
  cat > terraform/main.tf << EOF
# Main Terraform configuration for AI Orchestra

# Create a "badass" Vertex AI service account
resource "google_service_account" "vertex_ai_sa" {
  account_id   = "vertex-ai-badass"
  display_name = "Vertex AI Badass Service Account"
  description  = "Service account with extensive permissions for Vertex AI operations"
}

# Grant roles to the Vertex AI service account
resource "google_project_iam_member" "vertex_ai_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:\${google_service_account.vertex_ai_sa.email}"
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:\${google_service_account.vertex_ai_sa.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:\${google_service_account.vertex_ai_sa.email}"
}

resource "google_project_iam_member" "logging_admin" {
  project = var.project_id
  role    = "roles/logging.admin"
  member  = "serviceAccount:\${google_service_account.vertex_ai_sa.email}"
}

# Create a "badass" Gemini service account
resource "google_service_account" "gemini_sa" {
  account_id   = "gemini-badass"
  display_name = "Gemini Badass Service Account"
  description  = "Service account with extensive permissions for Gemini API operations"
}

# Grant roles to the Gemini service account
resource "google_project_iam_member" "gemini_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:\${google_service_account.gemini_sa.email}"
}

resource "google_project_iam_member" "gemini_service_usage" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:\${google_service_account.gemini_sa.email}"
}

# Set up Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions to impersonate the service accounts
resource "google_service_account_iam_binding" "workload_identity_binding_vertex" {
  service_account_id = google_service_account.vertex_ai_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/\${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
  ]
}

resource "google_service_account_iam_binding" "workload_identity_binding_gemini" {
  service_account_id = google_service_account.gemini_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/\${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
  ]
}

# Outputs
output "vertex_ai_service_account" {
  value = google_service_account.vertex_ai_sa.email
}

output "gemini_service_account" {
  value = google_service_account.gemini_sa.email
}

output "workload_identity_pool" {
  value = google_iam_workload_identity_pool.github_pool.name
}

output "workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github_provider.name
}
EOF
  
  log "SUCCESS" "Terraform configuration created"
}

# Initialize and apply Terraform
apply_terraform() {
  log "INFO" "Initializing Terraform..."
  
  # Change to terraform directory
  cd terraform
  
  # Initialize Terraform
  terraform init
  
  # Apply Terraform
  log "INFO" "Applying Terraform configuration..."
  terraform apply -auto-approve
  
  # Change back to root directory
  cd ..
  
  log "SUCCESS" "Terraform applied successfully"
}
# Create service account keys for the new service accounts
create_new_service_account_keys() {
  log "INFO" "Creating keys for new service accounts..."
  
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
  
  # Store project ID
  log "INFO" "Storing project ID in GitHub secrets..."
  echo "${PROJECT_ID}" | gh secret set "GCP_PROJECT_ID" --org "${GITHUB_ORG}" --body -
  
  # Store region
  log "INFO" "Storing region in GitHub secrets..."
  echo "${REGION}" | gh secret set "GCP_REGION" --org "${GITHUB_ORG}" --body -
  
  # Store Workload Identity Federation configuration
  log "INFO" "Storing Workload Identity Federation configuration in GitHub secrets..."
  WORKLOAD_IDENTITY_PROVIDER=$(terraform -chdir=terraform output -raw workload_identity_provider)
  echo "projects/${PROJECT_ID}/locations/global/workloadIdentityPools/github-pool/providers/github-provider" | \
    gh secret set "WORKLOAD_IDENTITY_PROVIDER" --org "${GITHUB_ORG}" --body -
  
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
          service_account: vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com
          project_id: ${PROJECT_ID}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy orchestra-api \\
            --source . \\
            --region \${{ secrets.GCP_REGION }} \\
            --platform managed \\
            --allow-unauthenticated
EOF
  
  log "SUCCESS" "GitHub Actions workflow created"
}

# Main function
main() {
  log "INFO" "Starting GCP infrastructure setup with real keys..."
  
  # Create service account key files
  create_service_account_key_files
  
  # Authenticate with GCP
  authenticate_with_gcp
  
  # Enable required APIs
  enable_apis
  
  # Create Terraform state bucket
  create_terraform_state_bucket
  
  # Set up Terraform
  setup_terraform
  
  # Initialize and apply Terraform
  apply_terraform
  
  # Create service account keys for the new service accounts
  create_new_service_account_keys
  
  # Store keys in Secret Manager
  store_keys_in_secret_manager
  
  # Store keys in GitHub secrets
  store_keys_in_github_secrets
  
  # Create GitHub Actions workflow
  create_github_actions_workflow
  
  log "SUCCESS" "GCP infrastructure setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Created service account key files"
  log "INFO" "2. Authenticated with GCP"
  log "INFO" "3. Enabled required APIs"
  log "INFO" "4. Created Terraform state bucket"
  log "INFO" "5. Set up Terraform configuration"
  log "INFO" "6. Applied Terraform to create service accounts and Workload Identity Federation"
  log "INFO" "7. Created service account keys for Vertex AI and Gemini"
  log "INFO" "8. Stored keys in Secret Manager"
  log "INFO" "9. Stored keys in GitHub secrets"
  log "INFO" "10. Created GitHub Actions workflow"
  
  log "INFO" "Next steps:"
  log "INFO" "1. Push the changes to GitHub"
  log "INFO" "2. Run the GitHub Actions workflow to deploy the application"
  log "INFO" "3. Verify that the deployment was successful"
}

# Execute main function
main