#!/bin/bash
# ==============================================================================
# Orchestra Deployment Script (deploy.sh)
# ==============================================================================
# Purpose: Deploys the Orchestra backend API and Phidata UI placeholder to
#          a specified GCP environment (dev or prod) using Terraform and Cloud Run.
# Usage: ./deploy.sh <environment>
#   Example: ./deploy.sh dev
#            ./deploy.sh prod
# Prerequisites:
#   - gcloud CLI installed and authenticated (user login + ADC)
#   - Terraform CLI installed
#   - Docker installed and running (client + daemon)
#   - .env file populated with necessary secrets (use setup_credentials_1password.sh)
#   - GCP Project configured (`gcloud config set project ...`)
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.
# set -o pipefail # Exit if any command in a pipeline fails
# set -u # Treat unset variables as an error

# --- Configuration ---
DEFAULT_ENV="dev"
TERRAFORM_DIR="infra/orchestra-terraform"
APP_DIR="." # Assuming Dockerfile is at the root, adjust if it's in apps/api
SCRIPT_DIR="scripts"
# Get commit sha for tagging
COMMIT_SHA_SHORT=$(git rev-parse --short HEAD)

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Helper Functions ---
info() {
    echo -e "${BLUE}INFO:${NC} $1"
}
warning() {
    echo -e "${YELLOW}WARN:${NC} $1"
}
error() {
    echo -e "${RED}ERROR:${NC} $1"
    exit 1
}
success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}
confirm() {
    # Prompt user for confirmation, default to No
    read -r -p "${YELLOW}CONFIRM:${NC} $1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}

# --- Script Execution ---

# 1. Validate Environment Argument
ENV="${1:-$DEFAULT_ENV}"
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    error "Invalid environment specified: '$ENV'. Must be 'dev' or 'prod'."
fi
info "Starting deployment for environment: ${CYAN}${ENV}${NC}"

# 2. Check Prerequisites
info "Checking required tools..."
command -v gcloud >/dev/null 2>&1 || error "gcloud CLI not found. Please install it."
command -v terraform >/dev/null 2>&1 || error "Terraform CLI not found. Please install it."
command -v docker >/dev/null 2>&1 || error "Docker CLI not found. Please install/enable it."
if ! docker ps > /dev/null 2>&1; then
    error "Docker daemon is not running or accessible. Please start/configure Docker."
fi
success "All required tools found."

# 3. Check GCP Authentication & Configuration
info "Checking GCP authentication and project..."
GCP_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)
GCP_PROJECT=$(gcloud config list --format='value(core.project)' 2>/dev/null)
if [ -z "$GCP_ACCOUNT" ]; then
    error "Not authenticated to Google Cloud. Run 'gcloud auth login' first."
fi
if [ -z "$GCP_PROJECT" ]; then
    error "GCP project not set. Run 'gcloud config set project YOUR_PROJECT_ID'."
fi
# Optionally check ADC credentials explicitly if needed by specific tools
# gcloud auth application-default print-access-token --quiet > /dev/null || error "Application Default Credentials (ADC) not configured. Run 'gcloud auth application-default login'."
success "Authenticated as ${CYAN}${GCP_ACCOUNT}${NC} for project ${CYAN}${GCP_PROJECT}${NC}."

# 4. Source Environment Variables (Optional but Recommended)
if [ -f ".env" ]; then
    info "Loading environment variables from .env file..."
    set -o allexport
    source ".env"
    set +o allexport
    success ".env file loaded."
else
    warning ".env file not found. Ensure required variables (API keys, etc.) are exported manually."
fi

# 5. Provision/Update Infrastructure with Terraform
info "Ensuring infrastructure is up-to-date with Terraform..."
if [ ! -d "$TERRAFORM_DIR" ]; then
    error "Terraform directory not found: $TERRAFORM_DIR"
fi

# Store current directory
pushd "$TERRAFORM_DIR" > /dev/null

info "Running Terraform init..."
terraform init -upgrade || error "Terraform init failed."

info "Selecting Terraform workspace: ${ENV}..."
terraform workspace select "$ENV" || terraform workspace new "$ENV" || error "Failed to select/create Terraform workspace."

info "Applying Terraform configuration for environment: ${ENV}..."
# Run plan first for review, unless specifically skipping
if [[ "$*" != *"--auto-approve"* ]]; then
    terraform plan "-var=env=${ENV}" || error "Terraform plan failed."
    if ! confirm "Apply the above Terraform plan?"; then
        error "Deployment aborted by user."
    fi
    terraform apply "-var=env=${ENV}" -auto-approve || error "Terraform apply failed."
else
    # Use auto-approve only if explicitly passed to this script
     terraform apply "-var=env=${ENV}" -auto-approve || error "Terraform apply failed."
fi
success "Terraform apply completed successfully."

# Get outputs needed for deployment (handle potential errors)
info "Retrieving deployment details from Terraform outputs..."
API_SERVICE_NAME=$(terraform output -raw orchestra_api_service_name 2>/dev/null || echo "")
UI_SERVICE_NAME=$(terraform output -raw phidata_ui_service_name 2>/dev/null || echo "")
VPC_CONNECTOR_ID=$(terraform output -raw vpc_connector_id 2>/dev/null || echo "") # Full ID: projects/.../connectors/...
GCP_REGION=$(terraform output -raw gcp_region 2>/dev/null || echo "us-central1") # Get region from output or default
ARTIFACT_REGISTRY_REPO=$(terraform output -raw artifact_registry_repo_url 2>/dev/null || echo "us-central1-docker.pkg.dev/${GCP_PROJECT}/orchestra") # Get repo URL or construct default

if [ -z "$API_SERVICE_NAME" ]; then
    error "Could not retrieve 'orchestra_api_service_name' from Terraform output. Ensure it's defined in outputs.tf and terraform apply succeeded."
fi
if [ -z "$UI_SERVICE_NAME" ]; then
    warning "Could not retrieve 'phidata_ui_service_name' from Terraform output. UI deployment might fail or use defaults."
fi
if [ -z "$VPC_CONNECTOR_ID" ]; then
    warning "Could not retrieve 'vpc_connector_id' from Terraform output. API deployment might fail if VPC access is required."
    VPC_CONNECTOR_ARG=""
else
    VPC_CONNECTOR_ARG="--vpc-connector=${VPC_CONNECTOR_ID} --vpc-egress=private-ranges-only" # Use full connector ID
    success "Using VPC Connector: ${VPC_CONNECTOR_ID}"
fi

# Return to original directory
popd > /dev/null

# 6. Setup PostgreSQL Schema (Only if Cloud SQL was created/updated)
# Ideally, check Terraform output or state, but for simplicity run it if script exists
if [ -f "$SCRIPT_DIR/setup_postgres_pgvector.py" ]; then
    info "Running PostgreSQL schema setup script..."
    # Ensure script has necessary DB connection env vars sourced from .env or set here
    python "$SCRIPT_DIR/setup_postgres_pgvector.py" || warning "PostgreSQL setup script failed. Check logs and run manually if needed."
    success "PostgreSQL setup script executed."
else
    warning "PostgreSQL setup script not found at $SCRIPT_DIR/setup_postgres_pgvector.py"
fi

# 7. Build and Push Orchestra API Docker Image
info "Building Orchestra API Docker image..."
IMAGE_TAG="${ARTIFACT_REGISTRY_REPO}/orchestrator:${ENV}-${COMMIT_SHA_SHORT}"
cd "$APP_DIR" || error "Application directory '$APP_DIR' not found."

docker build -t "$IMAGE_TAG" . || error "Docker build failed."
success "Docker image built: ${IMAGE_TAG}"

info "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker "$(echo "$ARTIFACT_REGISTRY_REPO" | cut -d'/' -f1)" --quiet || error "Failed to configure Docker authentication for Artifact Registry."

info "Pushing image to Artifact Registry..."
docker push "$IMAGE_TAG" || error "Docker push failed."
success "Image pushed successfully."
cd - > /dev/null # Go back to project root

# 8. Deploy Orchestra API to Cloud Run
info "Deploying Orchestra API service: ${API_SERVICE_NAME}..."
# Determine Log Level
if [[ "$ENV" == "prod" ]]; then
  LOG_LEVEL="INFO"
  # Consider adding --no-allow-unauthenticated for prod API
  ALLOW_UNAUTH_FLAG=""
else
  LOG_LEVEL="DEBUG"
  ALLOW_UNAUTH_FLAG="--allow-unauthenticated" # Allow public access for dev API
fi

# Construct Env Vars string (fetching sensitive values from Secret Manager via Cloud Run is preferred)
# This example sets non-sensitive vars directly, assuming sensitive ones like DB passwords
# are injected via secretKeyRef in Terraform's Cloud Run definition.
ENV_VARS="ENVIRONMENT=${ENV},LOG_LEVEL=${LOG_LEVEL},GCP_PROJECT_ID=${GCP_PROJECT},MEMORY_ENVIRONMENT=${ENV}" # Add other non-sensitive vars needed
# Add more vars: ,VAR1=value1,VAR2=value2

# Get the Service Account Email from Terraform output or variable
# Assume TF output exists:
RUN_SA_EMAIL=$(terraform -chdir="$TERRAFORM_DIR" output -raw cloud_run_sa_email 2>/dev/null || echo "")
if [ -z "$RUN_SA_EMAIL" ]; then
    error "Could not retrieve 'cloud_run_sa_email' from Terraform output. Needed for deployment."
fi

# Deploy API
gcloud run deploy "$API_SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --region="$GCP_REGION" \
    --platform=managed \
    --service-account="$RUN_SA_EMAIL" \
    --set-env-vars="$ENV_VARS" \
    $VPC_CONNECTOR_ARG \
    $ALLOW_UNAUTH_FLAG \
    --quiet || error "Cloud Run deployment failed for ${API_SERVICE_NAME}."
success "Orchestra API service deployed: ${API_SERVICE_NAME}"

# 9. Deploy/Update Phidata UI Placeholder to Cloud Run
if [ -n "$UI_SERVICE_NAME" ]; then
    info "Deploying/Updating Phidata UI service: ${UI_SERVICE_NAME}..."
    # Get API Service URL from gcloud after deployment (more reliable than TF output for this)
    API_SERVICE_URL=$(gcloud run services describe "$API_SERVICE_NAME" --platform=managed --region="$GCP_REGION" --format='value(status.url)')
    if [ -z "$API_SERVICE_URL" ]; then
        error "Failed to get URL for deployed API service: ${API_SERVICE_NAME}"
    fi

    # Assume the official image name (Verify this!)
    PHIDATA_UI_IMAGE="phidata/agent_ui:1.0.0"
    # Get the correct ENV var name required by the Phidata UI image
    PHIDATA_API_URL_VAR="PHIDATA_API_URL" # VERIFY THIS!

    UI_ENV_VARS="ENVIRONMENT=${ENV},${PHIDATA_API_URL_VAR}=${API_SERVICE_URL},PHIDATA_APP_NAME=Orchestra,PHIDATA_APP_DESCRIPTION=Orchestra AI,PHIDATA_TELEMETRY=false,PHIDATA_DEBUG=${ENV != 'prod'}"

    # Deploy UI
    gcloud run deploy "$UI_SERVICE_NAME" \
        --image="$PHIDATA_UI_IMAGE" \
        --region="$GCP_REGION" \
        --platform=managed \
        --set-env-vars="$UI_ENV_VARS" \
        --allow-unauthenticated \ # UI is typically public
        --quiet || error "Cloud Run deployment failed for ${UI_SERVICE_NAME}."
    success "Phidata UI service deployed: ${UI_SERVICE_NAME}"
else
    warning "Phidata UI service name not found. Skipping UI deployment."
fi

# 10. Final Verification (URLs)
info "Retrieving service URLs..."
SERVICE_URL_API=$(gcloud run services describe "$API_SERVICE_NAME" --platform=managed --region="$GCP_REGION" --format='value(status.url)' 2>/dev/null || echo "")
SERVICE_URL_UI=$(gcloud run services describe "$UI_SERVICE_NAME" --platform=managed --region="$GCP_REGION" --format='value(status.url)' 2>/dev/null || echo "")

if [ -n "$SERVICE_URL_API" ] || [ -n "$SERVICE_URL_UI" ]; then
    echo -e "\n${GREEN}=== Deployment Summary ===${NC}"
    if [ -n "$SERVICE_URL_API" ]; then
        echo -e "${GREEN}Orchestra API (${ENV}): ${SERVICE_URL_API}${NC}"
    fi
    if [ -n "$SERVICE_URL_UI" ]; then
        echo -e "${GREEN}Phidata Agent UI (${ENV}): ${SERVICE_URL_UI}${NC}"
    fi
    echo -e "${YELLOW}(Note: It might take a minute for new revisions to become fully available)${NC}"
else
    warning "Failed to retrieve service URLs after deployment. Check Cloud Run console."
fi

echo -e "\n${BLUE}=== Orchestra Deployment Script Finished ===${NC}"
exit 0
