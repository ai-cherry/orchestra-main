#!/bin/bash
# get_workload_identity_provider.sh - Script to get the correct Workload Identity Provider string for GitHub Actions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
POOL_NAME="github-wif-pool"
PROVIDER_NAME="github-provider"

echo -e "${BLUE}=== Getting Workload Identity Provider String for GitHub Actions ===${NC}"
echo -e "Project ID: ${PROJECT_ID}"
echo -e "Pool Name: ${POOL_NAME}"
echo -e "Provider Name: ${PROVIDER_NAME}"
echo

# Get the project number
echo -e "${YELLOW}Getting project number...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo -e "Project Number: ${PROJECT_NUMBER}"

# Construct the Workload Identity Provider string
echo -e "\n${YELLOW}Constructing Workload Identity Provider string...${NC}"
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo -e "${GREEN}Workload Identity Provider string:${NC}"
echo -e "${BLUE}${WIF_PROVIDER}${NC}"

# Check if the Workload Identity Pool exists
echo -e "\n${YELLOW}Checking if Workload Identity Pool exists...${NC}"
if gcloud iam workload-identity-pools describe $POOL_NAME \
  --project=$PROJECT_ID \
  --location="global" &>/dev/null; then
  echo -e "${GREEN}✓ Workload Identity Pool exists${NC}"
  
  # Check if the Workload Identity Provider exists
  echo -e "\n${YELLOW}Checking if Workload Identity Provider exists...${NC}"
  if gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --project=$PROJECT_ID \
    --location="global" \
    --workload-identity-pool=$POOL_NAME &>/dev/null; then
    echo -e "${GREEN}✓ Workload Identity Provider exists${NC}"
    
    # Get the actual Workload Identity Provider string from GCP
    echo -e "\n${YELLOW}Getting actual Workload Identity Provider string from GCP...${NC}"
    ACTUAL_WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
      --project=$PROJECT_ID \
      --location="global" \
      --workload-identity-pool=$POOL_NAME \
      --format="value(name)")
    echo -e "${GREEN}Actual Workload Identity Provider string:${NC}"
    echo -e "${BLUE}${ACTUAL_WIF_PROVIDER}${NC}"
  else
    echo -e "${RED}✗ Workload Identity Provider does not exist${NC}"
    echo -e "  You need to create the Workload Identity Provider first."
    echo -e "  Run the setup_workload_identity.sh script to create it."
  fi
else
  echo -e "${RED}✗ Workload Identity Pool does not exist${NC}"
  echo -e "  You need to create the Workload Identity Pool first."
  echo -e "  Run the setup_workload_identity.sh script to create it."
fi

echo -e "\n${BLUE}=== GitHub Actions Workflow Configuration ===${NC}"
echo -e "Add the following secrets to your GitHub repository:"
echo -e "${YELLOW}GCP_PROJECT_ID:${NC} $PROJECT_ID"
echo -e "${YELLOW}GCP_WORKLOAD_IDENTITY_PROVIDER:${NC} $WIF_PROVIDER"
echo -e "${YELLOW}GCP_SERVICE_ACCOUNT:${NC} [Your Service Account Email]"

echo -e "\n${BLUE}=== GitHub Actions Workflow Example ===${NC}"
echo -e "In your GitHub Actions workflow file (.github/workflows/deploy-mcp-server.yml):"
echo -e "${YELLOW}
- id: auth
  name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    token_format: 'access_token'
    workload_identity_provider: \${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: \${{ secrets.GCP_SERVICE_ACCOUNT }}
${NC}"