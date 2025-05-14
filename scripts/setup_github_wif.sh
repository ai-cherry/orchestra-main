#!/bin/bash
# setup_github_wif.sh - Set up Workload Identity Federation for GitHub Actions
#
# This script configures Workload Identity Federation between GitHub and Google Cloud,
# enabling keyless authentication for GitHub Actions workflows.
#
# Usage:
#   ./scripts/setup_github_wif.sh [GITHUB_REPO] [PROJECT_ID]
#
# Example:
#   ./scripts/setup_github_wif.sh "myorg/myrepo" "cherry-ai-project"

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
GITHUB_REPO=${1:-"ai-orchestra/orchestra-main"}
PROJECT_ID=${2:-"cherry-ai-project"}
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SERVICE_ACCOUNT="orchestra-wif-sa"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud command is not installed or not in PATH${NC}"
    echo "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Ensure user is authenticated with gcloud
echo -e "${BLUE}${BOLD}Checking authentication...${NC}"
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [[ -z "$ACCOUNT" ]]; then
    echo -e "${YELLOW}You are not authenticated with gcloud. Launching login...${NC}"
    gcloud auth login
fi

# Set the project
echo -e "${BLUE}${BOLD}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project "${PROJECT_ID}"

# Create the Workload Identity Pool if it doesn't exist
echo -e "${BLUE}${BOLD}Creating Workload Identity Pool...${NC}"
if ! gcloud iam workload-identity-pools describe "${POOL_ID}" --location="global" &>/dev/null; then
    gcloud iam workload-identity-pools create "${POOL_ID}" \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="Identity pool for GitHub Actions"
    echo -e "${GREEN}Created Workload Identity Pool: ${POOL_ID}${NC}"
else
    echo -e "${YELLOW}Workload Identity Pool ${POOL_ID} already exists.${NC}"
fi

# Get the workload identity pool ID
WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe "${POOL_ID}" \
    --location="global" \
    --format="value(name)")

# Create the Workload Identity Provider if it doesn't exist
echo -e "${BLUE}${BOLD}Creating Workload Identity Provider...${NC}"
if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --workload-identity-pool="${POOL_ID}" \
    --location="global" &>/dev/null; then
    
    gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
        --workload-identity-pool="${POOL_ID}" \
        --location="global" \
        --display-name="GitHub Actions Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    
    echo -e "${GREEN}Created Workload Identity Provider: ${PROVIDER_ID}${NC}"
else
    echo -e "${YELLOW}Workload Identity Provider ${PROVIDER_ID} already exists.${NC}"
fi

# Create the service account if it doesn't exist
echo -e "${BLUE}${BOLD}Creating service account...${NC}"
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
    gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
        --display-name="Service Account for GitHub Actions"
    echo -e "${GREEN}Created Service Account: ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
else
    echo -e "${YELLOW}Service Account ${SERVICE_ACCOUNT} already exists.${NC}"
fi

# Add IAM policy binding to allow the workload identity user to impersonate the service account
echo -e "${BLUE}${BOLD}Adding IAM policy binding...${NC}"
gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_REPO}"

echo -e "${GREEN}${BOLD}Successfully added IAM policy binding${NC}"

# Grant necessary roles to the service account
echo -e "${BLUE}${BOLD}Granting required roles to service account...${NC}"
roles=(
    "roles/run.admin"
    "roles/artifactregistry.writer"
    "roles/storage.admin"
    "roles/logging.logWriter"
    "roles/secretmanager.secretAccessor"
)

for role in "${roles[@]}"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}"
    echo -e "${GREEN}Granted ${role} to ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
done

# Output configuration for GitHub Actions workflow
echo -e "\n${BLUE}${BOLD}Workload Identity Federation setup complete!${NC}"
echo -e "${YELLOW}${BOLD}Use the following configuration in your GitHub Actions workflows:${NC}"
echo ""
echo -e "name: \"Authenticate to Google Cloud\""
echo -e "uses: google-github-actions/auth@v2"
echo -e "with:"
echo -e "  workload_identity_provider: 'projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}'"
echo -e "  service_account: '${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com'"
echo ""
echo -e "${GREEN}${BOLD}WIF setup complete for ${GITHUB_REPO} with project ${PROJECT_ID}${NC}"