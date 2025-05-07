#!/bin/bash
# deploy_gcp_infrastructure.sh - Script to deploy GCP infrastructure using Terraform
# This script initializes Terraform and applies the configuration

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting GCP infrastructure deployment...${NC}"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
  echo -e "${RED}Terraform is not installed. Installing...${NC}"
  
  # Install Terraform
  curl -fsSL https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip -o terraform.zip
  mkdir -p ~/bin
  unzip -o terraform.zip -d ~/bin
  chmod +x ~/bin/terraform
  export PATH="$HOME/bin:$PATH"
  
  # Verify installation
  if ! command -v ~/bin/terraform &> /dev/null; then
    echo -e "${RED}Failed to install Terraform${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Terraform installed successfully${NC}"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo -e "${RED}gcloud CLI is not installed${NC}"
  echo -e "${YELLOW}Please install the Google Cloud SDK and authenticate with gcloud auth login${NC}"
  exit 1
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

# Check if GCP_MASTER_SERVICE_JSON is set
if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
  echo -e "${RED}GCP_MASTER_SERVICE_JSON is not set${NC}"
  echo -e "${YELLOW}Please set the GCP_MASTER_SERVICE_JSON environment variable with the master service account key${NC}"
  echo -e "${YELLOW}You can run: export GCP_MASTER_SERVICE_JSON=\$(cat /path/to/key.json)${NC}"
  exit 1
fi

# Authenticate with GCP
echo -e "${GREEN}Authenticating with GCP...${NC}"
echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/master-key.json
gcloud auth activate-service-account --key-file=/tmp/master-key.json
rm /tmp/master-key.json

# Run the fix_terraform_config.sh script if it exists
if [ -f "fix_terraform_config.sh" ]; then
  echo -e "${GREEN}Running fix_terraform_config.sh...${NC}"
  chmod +x fix_terraform_config.sh
  ./fix_terraform_config.sh
else
  echo -e "${YELLOW}fix_terraform_config.sh not found. Skipping Terraform configuration fix.${NC}"
fi

# Create the create_badass_service_keys.sh script if it doesn't exist
if [ ! -f "create_badass_service_keys.sh" ]; then
  echo -e "${YELLOW}create_badass_service_keys.sh not found. Creating it...${NC}"
  ./fix_terraform_config.sh
fi

# Initialize Terraform
echo -e "${GREEN}Initializing Terraform...${NC}"
cd terraform
terraform init

# Plan Terraform changes
echo -e "${GREEN}Planning Terraform changes...${NC}"
terraform plan -var="project_id=${GCP_PROJECT_ID}" -var="region=${REGION}" -var="env=${ENV}" -out=tfplan

# Ask for confirmation before applying
echo -e "${YELLOW}Do you want to apply these changes? (y/n)${NC}"
read -r CONFIRM
if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
  echo -e "${RED}Deployment cancelled${NC}"
  exit 0
fi

# Apply Terraform changes
echo -e "${GREEN}Applying Terraform changes...${NC}"
terraform apply tfplan

# Create service account keys
echo -e "${GREEN}Creating service account keys...${NC}"
cd ..
chmod +x create_badass_service_keys.sh
./create_badass_service_keys.sh

# Update GitHub secrets
if [ -f "scripts/update_github_org_secrets.sh" ]; then
  echo -e "${GREEN}Updating GitHub secrets...${NC}"
  chmod +x scripts/update_github_org_secrets.sh
  ./scripts/update_github_org_secrets.sh
else
  echo -e "${YELLOW}scripts/update_github_org_secrets.sh not found. Skipping GitHub secrets update.${NC}"
fi

echo -e "${GREEN}GCP infrastructure deployment completed!${NC}"
echo -e "${GREEN}Next steps:${NC}"
echo -e "${GREEN}1. Verify the deployment in the GCP console${NC}"
echo -e "${GREEN}2. Check that GitHub secrets are updated${NC}"
echo -e "${GREEN}3. Test the infrastructure with a sample application${NC}"