 the #!/bin/bash
# Setup Workload Identity Federation for GitHub Actions
# This script creates and configures Workload Identity Federation for GitHub Actions
# to securely authenticate with GCP without using service account keys.

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
REPO_OWNER=${REPO_OWNER:-"your-github-org"}  # Default value, override with env var
REPO_NAME=${REPO_NAME:-"orchestra-main"}      # Default value, override with env var
SERVICE_ACCOUNT_NAME="github-actions-wif"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"

section "Workload Identity Federation Setup for GitHub Actions"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
if [[ -z "$ACCOUNT" ]]; then
    error "You are not logged in to gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

echo "Currently authenticated as: $ACCOUNT"
echo "Project ID: $PROJECT_ID"
echo "GitHub Repository: $REPO_OWNER/$REPO_NAME"

if [[ -z "$REPO_OWNER" || "$REPO_OWNER" == "your-github-org" ]]; then
    read -p "Enter your GitHub organization or username: " REPO_OWNER
fi

if [[ -z "$REPO_NAME" || "$REPO_NAME" == "orchestra-main" ]]; then
    read -p "Enter your GitHub repository name: " REPO_NAME
fi

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
section "Enabling required APIs"
echo "Enabling IAM Credentials API..."
gcloud services enable iamcredentials.googleapis.com
echo "Enabling Service Account Credentials API..."
gcloud services enable sts.googleapis.com
echo "Enabling Security Token Service API..."
gcloud services enable cloudresourcemanager.googleapis.com

# Create Workload Identity Pool
section "Creating Workload Identity Pool"
echo "Creating pool $POOL_NAME..."
gcloud iam workload-identity-pools create $POOL_NAME \
    --location="global" \
    --description="Pool for GitHub Actions" \
    --display-name="GitHub Actions Pool" \
    --project=$PROJECT_ID

# Get the Workload Identity Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" \
    --format="value(name)" \
    --project=$PROJECT_ID)

success "Created Workload Identity Pool: $POOL_ID"

# Create Workload Identity Provider
section "Creating Workload Identity Provider"
echo "Creating provider $PROVIDER_NAME..."
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --project=$PROJECT_ID

# Get the Workload Identity Provider ID
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --format="value(name)" \
    --project=$PROJECT_ID)

success "Created Workload Identity Provider: $PROVIDER_ID"

# Create Service Account
section "Creating Service Account"
echo "Creating service account $SERVICE_ACCOUNT_NAME..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="GitHub Actions WIF Service Account" \
    --project=$PROJECT_ID

# Grant necessary roles to the service account
section "Granting roles to Service Account"
echo "Granting roles to $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com..."

# Cloud Run Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Artifact Registry Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

# Storage Admin role (for Terraform state)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Secret Manager Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

# Service Account User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Allow GitHub Actions to impersonate the service account
section "Allowing GitHub Actions to impersonate Service Account"
echo "Setting up impersonation for GitHub repository: $REPO_OWNER/$REPO_NAME..."

gcloud iam service-accounts add-iam-policy-binding \
    $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO_OWNER}/${REPO_NAME}"

success "Service account impersonation configured"

# Output the configuration values for GitHub Actions
section "GitHub Actions Configuration"
echo "Add the following secrets to your GitHub repository:"
echo ""
echo "WIF_PROVIDER_ID: projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo "WIF_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "Example GitHub Actions workflow configuration:"
echo ""
cat << EOF
- name: Authenticate to Google Cloud with OIDC
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: \${{ secrets.WIF_PROVIDER_ID }}
    service_account: \${{ secrets.WIF_SERVICE_ACCOUNT }}
    token_format: access_token
EOF

section "Setup Complete"
success "Workload Identity Federation setup completed successfully!"
echo "You can now use GitHub Actions to deploy to GCP without service account keys."