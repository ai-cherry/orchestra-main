#!/bin/bash
# setup_github_wif_secrets.sh - Script to set up GitHub repository secrets for Workload Identity Federation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
REGION=${2:-"us-central1"}
GITHUB_REPO=${3:-"ai-cherry/orchestra-main"}
POOL_ID=${4:-"github-pool"}
PROVIDER_ID=${5:-"github-provider"}
SERVICE_ACCOUNT_ID=${6:-"github-actions-sa"}

echo -e "${GREEN}Setting up GitHub repository secrets for Workload Identity Federation...${NC}"
echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}GitHub Repository: ${GITHUB_REPO}${NC}"
echo -e "${YELLOW}Pool ID: ${POOL_ID}${NC}"
echo -e "${YELLOW}Provider ID: ${PROVIDER_ID}${NC}"
echo -e "${YELLOW}Service Account ID: ${SERVICE_ACCOUNT_ID}${NC}"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Visit https://cli.github.com/ for installation instructions.${NC}"
    exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
    echo -e "${RED}You are not authenticated with GitHub CLI. Please run 'gh auth login' first.${NC}"
    exit 1
fi

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Google Cloud SDK (gcloud) is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Visit https://cloud.google.com/sdk/docs/install for installation instructions.${NC}"
    exit 1
fi

# Check if user is authenticated with gcloud CLI
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}You are not authenticated with gcloud CLI. Please run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Get the project number
echo -e "${GREEN}Getting project number...${NC}"
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
echo -e "${GREEN}Project number: ${PROJECT_NUMBER}${NC}"

# Construct the Workload Identity Provider resource name
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
echo -e "${GREEN}Workload Identity Provider: ${WIF_PROVIDER}${NC}"

# Construct the service account email
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
echo -e "${GREEN}Service Account Email: ${SERVICE_ACCOUNT_EMAIL}${NC}"

# Set GitHub repository secrets
echo -e "${GREEN}Setting GitHub repository secrets...${NC}"

echo -e "${YELLOW}Setting GCP_PROJECT_ID secret...${NC}"
echo -n "${PROJECT_ID}" | gh secret set GCP_PROJECT_ID --repo ${GITHUB_REPO}

echo -e "${YELLOW}Setting GCP_REGION secret...${NC}"
echo -n "${REGION}" | gh secret set GCP_REGION --repo ${GITHUB_REPO}

echo -e "${YELLOW}Setting GCP_WORKLOAD_IDENTITY_PROVIDER secret...${NC}"
echo -n "${WIF_PROVIDER}" | gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --repo ${GITHUB_REPO}

echo -e "${YELLOW}Setting GCP_SERVICE_ACCOUNT secret...${NC}"
echo -n "${SERVICE_ACCOUNT_EMAIL}" | gh secret set GCP_SERVICE_ACCOUNT --repo ${GITHUB_REPO}

echo -e "${GREEN}GitHub repository secrets have been set up successfully!${NC}"
echo -e "${GREEN}You can now use Workload Identity Federation in your GitHub Actions workflows.${NC}"
