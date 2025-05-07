#!/bin/bash
# fix_terraform_config.sh - Script to fix Terraform configuration issues
# This script consolidates duplicate configurations and fixes missing modules

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Terraform configuration fix...${NC}"

# Create backup directory
BACKUP_DIR="terraform_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup current Terraform files
echo -e "${GREEN}Backing up current Terraform files...${NC}"
cp -r terraform/* "$BACKUP_DIR/"
echo -e "${GREEN}Backup completed${NC}"

# Fix duplicate backend configuration
echo -e "${GREEN}Fixing duplicate backend configuration...${NC}"
if grep -q "backend \"gcs\"" terraform/main.tf; then
  echo -e "${YELLOW}Removing backend configuration from main.tf${NC}"
  sed -i '/backend "gcs" {/,/}/d' terraform/main.tf
fi

# Fix duplicate variable declarations
echo -e "${GREEN}Fixing duplicate variable declarations...${NC}"
# Remove duplicate variables from main.tf
if grep -q "variable \"project_id\"" terraform/main.tf; then
  echo -e "${YELLOW}Removing duplicate variable declarations from main.tf${NC}"
  sed -i '/variable "project_id" {/,/}/d' terraform/main.tf
  sed -i '/variable "region" {/,/}/d' terraform/main.tf
  sed -i '/variable "env" {/,/}/d' terraform/main.tf
fi

# Fix duplicate provider configurations
echo -e "${GREEN}Fixing duplicate provider configurations...${NC}"
# Remove duplicate provider configurations from provider_google_sdk.tf
if [ -f terraform/provider_google_sdk.tf ]; then
  echo -e "${YELLOW}Removing duplicate provider configurations from provider_google_sdk.tf${NC}"
  sed -i '/provider "google" {/,/}/d' terraform/provider_google_sdk.tf
  sed -i '/provider "google-beta" {/,/}/d' terraform/provider_google_sdk.tf
fi

# Remove duplicate provider configurations from providers.tf
if [ -f terraform/providers.tf ]; then
  echo -e "${YELLOW}Removing duplicate provider configurations from providers.tf${NC}"
  sed -i '/provider "google" {/,/}/d' terraform/providers.tf
  sed -i '/provider "google-beta" {/,/}/d' terraform/providers.tf
fi

# Fix duplicate required providers configuration
echo -e "${GREEN}Fixing duplicate required providers configuration...${NC}"
if grep -q "required_providers" terraform/provider_github_sdk.tf; then
  echo -e "${YELLOW}Removing duplicate required providers from provider_github_sdk.tf${NC}"
  sed -i '/required_providers {/,/}/d' terraform/provider_github_sdk.tf
fi
if grep -q "required_providers" terraform/versions.tf; then
  echo -e "${YELLOW}Removing duplicate required providers from versions.tf${NC}"
  sed -i '/required_providers {/,/}/d' terraform/versions.tf
fi

# Fix duplicate workload identity pool resources
echo -e "${GREEN}Fixing duplicate workload identity pool resources...${NC}"
if grep -q "google_iam_workload_identity_pool" terraform/github_repositories.tf; then
  echo -e "${YELLOW}Removing duplicate workload identity pool from github_repositories.tf${NC}"
  sed -i '/resource "google_iam_workload_identity_pool" "github_pool" {/,/}/d' terraform/github_repositories.tf
  sed -i '/resource "google_iam_workload_identity_pool_provider" "github_provider" {/,/}/d' terraform/github_repositories.tf
fi

# Create missing env-validation module directory
echo -e "${GREEN}Creating missing env-validation module directory...${NC}"
mkdir -p terraform/modules/env-validation
cat > terraform/modules/env-validation/main.tf << 'EOF'
# Environment validation module
# This module validates that required environment variables are set

variable "github_token" {
  description = "GitHub token for authentication"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.github_token) > 0
    error_message = "GitHub token must be provided."
  }
}

variable "github_owner" {
  description = "GitHub organization or user name"
  type        = string
  
  validation {
    condition     = length(var.github_owner) > 0
    error_message = "GitHub owner must be provided."
  }
}

# Output validation result
output "validation_passed" {
  value = "true"
}
EOF

echo -e "${GREEN}Created env-validation module${NC}"

# Create missing create_badass_service_keys.sh script
echo -e "${GREEN}Creating missing create_badass_service_keys.sh script...${NC}"
cat > create_badass_service_keys.sh << 'EOF'
#!/bin/bash
# create_badass_service_keys.sh - Script to create service account keys for Vertex AI and Gemini

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
: "${REGION:=us-west4}"
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

# Create Vertex AI service account and key
create_vertex_key() {
  log "INFO" "Creating Vertex AI service account and key..."
  
  # Service account name
  VERTEX_SA_NAME="vertex-power-user"
  VERTEX_SA_EMAIL="${VERTEX_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  # Create service account if it doesn't exist
  if gcloud iam service-accounts describe "${VERTEX_SA_EMAIL}" --project="${GCP_PROJECT_ID}" &> /dev/null; then
    log "INFO" "Vertex AI service account already exists"
  else
    log "INFO" "Creating Vertex AI service account..."
    gcloud iam service-accounts create "${VERTEX_SA_NAME}" \
      --display-name="Vertex AI Power User" \
      --description="Service account with extensive permissions for Vertex AI operations" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Assign roles to the service account
  log "INFO" "Assigning roles to Vertex AI service account..."
  VERTEX_ROLES=(
    "roles/aiplatform.admin"
    "roles/aiplatform.user"
    "roles/storage.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/iam.serviceAccountTokenCreator"
    "roles/compute.admin"
    "roles/serviceusage.serviceUsageAdmin"
  )
  
  for role in "${VERTEX_ROLES[@]}"; do
    log "INFO" "  - Assigning role: ${role}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${VERTEX_SA_EMAIL}" \
      --role="${role}" \
      --quiet
  done
  
  # Create service account key
  log "INFO" "Creating Vertex AI service account key..."
  KEY_FILE=$(mktemp)
  gcloud iam service-accounts keys create "${KEY_FILE}" \
    --iam-account="${VERTEX_SA_EMAIL}" \
    --project="${GCP_PROJECT_ID}"
  
  # Store key in Secret Manager
  log "INFO" "Storing Vertex AI key in Secret Manager..."
  if gcloud secrets describe "vertex-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "vertex-power-key" \
      --data-file="${KEY_FILE}" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "vertex-power-key" \
      --data-file="${KEY_FILE}" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Store key in GitHub secrets if GitHub CLI is available
  if command -v gh &> /dev/null; then
    log "INFO" "Storing Vertex AI key in GitHub secrets..."
    VERTEX_KEY=$(cat "${KEY_FILE}")
    gh secret set "VERTEX_POWER_KEY" --org "${GITHUB_ORG}" --body "${VERTEX_KEY}"
  fi
  
  # Securely remove the key file
  shred -u "${KEY_FILE}"
  
  log "SUCCESS" "Vertex AI service account and key created successfully"
}

# Create Gemini service account and key
create_gemini_key() {
  log "INFO" "Creating Gemini service account and key..."
  
  # Service account name
  GEMINI_SA_NAME="gemini-power-user"
  GEMINI_SA_EMAIL="${GEMINI_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  # Create service account if it doesn't exist
  if gcloud iam service-accounts describe "${GEMINI_SA_EMAIL}" --project="${GCP_PROJECT_ID}" &> /dev/null; then
    log "INFO" "Gemini service account already exists"
  else
    log "INFO" "Creating Gemini service account..."
    gcloud iam service-accounts create "${GEMINI_SA_NAME}" \
      --display-name="Gemini Power User" \
      --description="Service account with extensive permissions for Gemini operations" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Assign roles to the service account
  log "INFO" "Assigning roles to Gemini service account..."
  GEMINI_ROLES=(
    "roles/aiplatform.admin"
    "roles/aiplatform.user"
    "roles/storage.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/iam.serviceAccountTokenCreator"
    "roles/serviceusage.serviceUsageAdmin"
  )
  
  for role in "${GEMINI_ROLES[@]}"; do
    log "INFO" "  - Assigning role: ${role}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${GEMINI_SA_EMAIL}" \
      --role="${role}" \
      --quiet
  done
  
  # Create service account key
  log "INFO" "Creating Gemini service account key..."
  KEY_FILE=$(mktemp)
  gcloud iam service-accounts keys create "${KEY_FILE}" \
    --iam-account="${GEMINI_SA_EMAIL}" \
    --project="${GCP_PROJECT_ID}"
  
  # Store key in Secret Manager
  log "INFO" "Storing Gemini key in Secret Manager..."
  if gcloud secrets describe "gemini-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    gcloud secrets versions add "gemini-power-key" \
      --data-file="${KEY_FILE}" \
      --project="${GCP_PROJECT_ID}"
  else
    gcloud secrets create "gemini-power-key" \
      --data-file="${KEY_FILE}" \
      --project="${GCP_PROJECT_ID}"
  fi
  
  # Store key in GitHub secrets if GitHub CLI is available
  if command -v gh &> /dev/null; then
    log "INFO" "Storing Gemini key in GitHub secrets..."
    GEMINI_KEY=$(cat "${KEY_FILE}")
    gh secret set "GEMINI_POWER_KEY" --org "${GITHUB_ORG}" --body "${GEMINI_KEY}"
  fi
  
  # Securely remove the key file
  shred -u "${KEY_FILE}"
  
  log "SUCCESS" "Gemini service account and key created successfully"
}

# Main function
main() {
  log "INFO" "Starting service account key creation..."
  
  # Create Vertex AI service account and key
  create_vertex_key
  
  # Create Gemini service account and key
  create_gemini_key
  
  log "SUCCESS" "Service account keys created successfully!"
}

# Execute main function
main
EOF

chmod +x create_badass_service_keys.sh
echo -e "${GREEN}Created create_badass_service_keys.sh script${NC}"

echo -e "${GREEN}Terraform configuration fix completed!${NC}"
echo -e "${GREEN}You can now run 'cd terraform && terraform init' to initialize Terraform${NC}"