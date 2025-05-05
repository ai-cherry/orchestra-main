#!/bin/bash
# Script to apply Terraform configurations in sequence using the temporary admin SA key
# This script follows the order: common -> dev -> prod environments

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
COMMON_DIR="infra/terraform/common"
DEV_DIR="infra/dev"
PROD_DIR="infra/prod"

echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}      TERRAFORM APPLY SEQUENCE FOR PROJECT: ${PROJECT_ID}      ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# 1. Apply 'common' environment
echo -e "\n${YELLOW}${BOLD}STEP 1: Applying 'common' environment...${NC}"
cd "${COMMON_DIR}" || mkdir -p "${COMMON_DIR}" && cd "${COMMON_DIR}"
echo "Initializing Terraform..."
terraform init -reconfigure

echo "Planning and applying Terraform configuration..."
terraform apply -auto-approve -var="project_id=${PROJECT_ID}"

# 2. Get WIF outputs from common deployment
echo -e "\n${YELLOW}${BOLD}STEP 2: Retrieving Workload Identity Federation outputs...${NC}"
WIF_PROVIDER=$(terraform output -raw workload_identity_provider 2>/dev/null || echo "Not available")
SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "Not available")

echo -e "${GREEN}WIF Provider: ${WIF_PROVIDER}${NC}"
echo -e "${GREEN}Service Account: ${SERVICE_ACCOUNT}${NC}"

# Store values for later use in GitHub secrets
echo "${WIF_PROVIDER}" > /tmp/wif_provider.txt
echo "${SERVICE_ACCOUNT}" > /tmp/service_account.txt

# Return to root directory
cd /workspaces/orchestra-main

# 3. Apply 'dev' environment
echo -e "\n${YELLOW}${BOLD}STEP 3: Applying 'dev' environment...${NC}"
cd "${DEV_DIR}" || mkdir -p "${DEV_DIR}" && cd "${DEV_DIR}"
echo "Initializing Terraform..."
terraform init -reconfigure

echo "Planning and applying Terraform configuration..."
terraform apply -auto-approve -var="project_id=${PROJECT_ID}"

# Return to root directory
cd /workspaces/orchestra-main

# 4. Apply 'prod' environment
echo -e "\n${YELLOW}${BOLD}STEP 4: Applying 'prod' environment...${NC}"
cd "${PROD_DIR}" || mkdir -p "${PROD_DIR}" && cd "${PROD_DIR}"
echo "Initializing Terraform..."
terraform init -reconfigure

echo "Planning and applying Terraform configuration..."
terraform apply -auto-approve -var="project_id=${PROJECT_ID}"

# Return to root directory
cd /workspaces/orchestra-main

echo -e "\n${GREEN}${BOLD}Terraform apply sequence completed successfully!${NC}"
echo -e "${BLUE}${BOLD}------------------------------------------------------------${NC}"
echo -e "${YELLOW}WIF Provider: ${WIF_PROVIDER}${NC}"
echo -e "${YELLOW}Service Account: ${SERVICE_ACCOUNT}${NC}"
echo -e "${BLUE}${BOLD}------------------------------------------------------------${NC}"

echo -e "\n${BOLD}Next steps:${NC}"
echo "1. Update GitHub secrets with WIF values"
echo "2. Update GitHub Actions workflows to use WIF authentication"
echo "3. Create service account keys for Vertex and Gemini"
