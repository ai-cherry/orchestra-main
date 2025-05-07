#!/bin/bash
# update_github_org_secrets.sh - Script to update GitHub organization secrets with GCP service account information
# This script updates GitHub organization secrets with GCP project information and service account keys

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting GitHub organization secrets update...${NC}"

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${REGION:=us-west4}"
: "${ENV:=dev}"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo -e "${RED}GitHub CLI is not installed${NC}"
  echo -e "${YELLOW}Installing GitHub CLI...${NC}"
  
  # Install GitHub CLI
  type -p curl >/dev/null || (apt update && apt install curl -y)
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  sudo apt update
  sudo apt install gh -y
  
  # Verify installation
  if ! command -v gh &> /dev/null; then
    echo -e "${RED}Failed to install GitHub CLI${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}GitHub CLI installed successfully${NC}"
fi

# Check if GITHUB_TOKEN is set
if [ -z "${GITHUB_TOKEN}" ]; then
  echo -e "${RED}GITHUB_TOKEN is not set${NC}"
  echo -e "${YELLOW}Please set the GITHUB_TOKEN environment variable with a GitHub personal access token${NC}"
  echo -e "${YELLOW}You can run: export GITHUB_TOKEN=your_github_token${NC}"
  exit 1
fi

# Authenticate with GitHub
echo -e "${GREEN}Authenticating with GitHub...${NC}"
echo "${GITHUB_TOKEN}" | gh auth login --with-token

# Verify GitHub authentication
if ! gh auth status &>/dev/null; then
  echo -e "${RED}Failed to authenticate with GitHub${NC}"
  exit 1
fi

echo -e "${GREEN}Successfully authenticated with GitHub${NC}"

# Update GitHub organization secrets
echo -e "${GREEN}Updating GitHub organization secrets...${NC}"

# Set GCP project ID
echo -e "${GREEN}Setting GCP_PROJECT_ID secret...${NC}"
gh secret set "GCP_PROJECT_ID" --org "${GITHUB_ORG}" --body "${GCP_PROJECT_ID}"

# Set GCP region
echo -e "${GREEN}Setting GCP_REGION secret...${NC}"
gh secret set "GCP_REGION" --org "${GITHUB_ORG}" --body "${REGION}"

# Set environment
echo -e "${GREEN}Setting GCP_ENV secret...${NC}"
gh secret set "GCP_ENV" --org "${GITHUB_ORG}" --body "${ENV}"

# Set Workload Identity Federation provider ID if available
if [ -f "/tmp/wif_provider.txt" ]; then
  PROVIDER_ID=$(cat /tmp/wif_provider.txt)
  echo -e "${GREEN}Setting WIF_PROVIDER_ID secret...${NC}"
  gh secret set "WIF_PROVIDER_ID" --org "${GITHUB_ORG}" --body "${PROVIDER_ID}"
fi

# Set service account emails
for SA_NAME in "github-actions" "orchestrator-api" "phidata-agent-ui" "vertex-power-user" "gemini-power-user"; do
  SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  SECRET_NAME=$(echo "${SA_NAME}" | tr '-' '_' | tr '[:lower:]' '[:upper:]')_SERVICE_ACCOUNT
  
  echo -e "${GREEN}Setting ${SECRET_NAME} secret...${NC}"
  gh secret set "${SECRET_NAME}" --org "${GITHUB_ORG}" --body "${SA_EMAIL}"
done

# Set service account keys if available
if gcloud secrets versions access latest --secret="vertex-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo -e "${GREEN}Setting VERTEX_POWER_KEY secret...${NC}"
  VERTEX_KEY=$(gcloud secrets versions access latest --secret="vertex-power-key" --project="${GCP_PROJECT_ID}")
  gh secret set "VERTEX_POWER_KEY" --org "${GITHUB_ORG}" --body "${VERTEX_KEY}"
fi

if gcloud secrets versions access latest --secret="gemini-power-key" --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo -e "${GREEN}Setting GEMINI_POWER_KEY secret...${NC}"
  GEMINI_KEY=$(gcloud secrets versions access latest --secret="gemini-power-key" --project="${GCP_PROJECT_ID}")
  gh secret set "GEMINI_POWER_KEY" --org "${GITHUB_ORG}" --body "${GEMINI_KEY}"
fi

# Set master service account key if available
if [ -n "${GCP_MASTER_SERVICE_JSON}" ]; then
  echo -e "${GREEN}Setting GCP_MASTER_SERVICE_JSON secret...${NC}"
  gh secret set "GCP_MASTER_SERVICE_JSON" --org "${GITHUB_ORG}" --body "${GCP_MASTER_SERVICE_JSON}"
fi

echo -e "${GREEN}GitHub organization secrets updated successfully!${NC}"
echo -e "${GREEN}The following secrets have been set:${NC}"
echo -e "${GREEN}- GCP_PROJECT_ID${NC}"
echo -e "${GREEN}- GCP_REGION${NC}"
echo -e "${GREEN}- GCP_ENV${NC}"
echo -e "${GREEN}- WIF_PROVIDER_ID (if available)${NC}"
echo -e "${GREEN}- GITHUB_ACTIONS_SERVICE_ACCOUNT${NC}"
echo -e "${GREEN}- ORCHESTRATOR_API_SERVICE_ACCOUNT${NC}"
echo -e "${GREEN}- PHIDATA_AGENT_UI_SERVICE_ACCOUNT${NC}"
echo -e "${GREEN}- VERTEX_POWER_USER_SERVICE_ACCOUNT${NC}"
echo -e "${GREEN}- GEMINI_POWER_USER_SERVICE_ACCOUNT${NC}"
echo -e "${GREEN}- VERTEX_POWER_KEY (if available)${NC}"
echo -e "${GREEN}- GEMINI_POWER_KEY (if available)${NC}"
echo -e "${GREEN}- GCP_MASTER_SERVICE_JSON (if available)${NC}"