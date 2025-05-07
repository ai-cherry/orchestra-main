#!/bin/bash
# setup_infrastructure.sh - Master script to set up the entire infrastructure
# This script makes all the scripts executable and runs the deployment process

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Orchestra infrastructure setup...${NC}"

# Make all scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x fix_terraform_config.sh
chmod +x deploy_gcp_infrastructure.sh
chmod +x update_github_org_secrets.sh
chmod +x orchestra_wif_master.sh
if [ -f "create_master_service_key.sh" ]; then
  chmod +x create_master_service_key.sh
fi

# Check if GCP_PROJECT_ID is set
if [ -z "${GCP_PROJECT_ID}" ]; then
  echo -e "${YELLOW}GCP_PROJECT_ID is not set. Using default value: cherry-ai-project${NC}"
  export GCP_PROJECT_ID="cherry-ai-project"
fi

# Check if REGION is set
if [ -z "${REGION}" ]; then
  echo -e "${YELLOW}REGION is not set. Using default value: us-west4${NC}"
  export REGION="us-west4"
fi

# Check if ENV is set
if [ -z "${ENV}" ]; then
  echo -e "${YELLOW}ENV is not set. Using default value: dev${NC}"
  export ENV="dev"
fi

# Check if GITHUB_ORG is set
if [ -z "${GITHUB_ORG}" ]; then
  echo -e "${YELLOW}GITHUB_ORG is not set. Using default value: ai-cherry${NC}"
  export GITHUB_ORG="ai-cherry"
fi

# Check if GITHUB_REPO is set
if [ -z "${GITHUB_REPO}" ]; then
  echo -e "${YELLOW}GITHUB_REPO is not set. Using default value: orchestra-main${NC}"
  export GITHUB_REPO="orchestra-main"
fi

# Check if GITHUB_TOKEN is set
if [ -z "${GITHUB_TOKEN}" ]; then
  echo -e "${RED}GITHUB_TOKEN is not set${NC}"
  echo -e "${YELLOW}Please set the GITHUB_TOKEN environment variable with a GitHub personal access token${NC}"
  echo -e "${YELLOW}You can run: export GITHUB_TOKEN=your_github_token${NC}"
  exit 1
fi

# Check if GCP_MASTER_SERVICE_JSON is set
if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
  echo -e "${YELLOW}GCP_MASTER_SERVICE_JSON is not set. Checking if create_master_service_key.sh exists...${NC}"
  if [ -f "create_master_service_key.sh" ]; then
    echo -e "${GREEN}Running create_master_service_key.sh to create a master service account key...${NC}"
    ./create_master_service_key.sh
  else
    echo -e "${RED}GCP_MASTER_SERVICE_JSON is not set and create_master_service_key.sh does not exist${NC}"
    echo -e "${YELLOW}Please set the GCP_MASTER_SERVICE_JSON environment variable with the master service account key${NC}"
    echo -e "${YELLOW}You can run: export GCP_MASTER_SERVICE_JSON=\$(cat /path/to/key.json)${NC}"
    exit 1
  fi
fi

# Run the fix_terraform_config.sh script
echo -e "${GREEN}Running fix_terraform_config.sh...${NC}"
./fix_terraform_config.sh

# Run the deploy_gcp_infrastructure.sh script
echo -e "${GREEN}Running deploy_gcp_infrastructure.sh...${NC}"
./deploy_gcp_infrastructure.sh

# Run the update_github_org_secrets.sh script
echo -e "${GREEN}Running update_github_org_secrets.sh...${NC}"
./update_github_org_secrets.sh

# Run the orchestra_wif_master.sh script
echo -e "${GREEN}Running orchestra_wif_master.sh...${NC}"
./orchestra_wif_master.sh

echo -e "${GREEN}AI Orchestra infrastructure setup completed!${NC}"
echo -e "${GREEN}Please check the INFRASTRUCTURE_SETUP.md file for more information.${NC}"