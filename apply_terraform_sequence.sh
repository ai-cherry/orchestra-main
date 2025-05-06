#!/bin/bash
# Script to apply Terraform configurations in sequence

set -e

# Configuration
export PROJECT_ID="cherry-ai-project"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export TF_STATE_BUCKET="tfstate-cherry-ai-project-orchestra"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Starting Terraform Sequential Deployment ===${NC}"

# Initialize and apply common environment
echo -e "${YELLOW}Applying common environment configuration...${NC}"
cd infra/terraform/gcp/environments/common
terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="prefix=common"
terraform apply -auto-approve

# Extract WIF values for later use
WIF_PROVIDER=$(terraform output -raw workload_identity_provider)
WIF_SERVICE_ACCOUNT=$(terraform output -raw service_account_email)

cd ../../../..

# Apply dev environment configuration
echo -e "${YELLOW}Applying dev environment configuration...${NC}"
cd environments/dev
terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="prefix=dev"
terraform apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="wif_provider=${WIF_PROVIDER}" \
  -var="service_account=${WIF_SERVICE_ACCOUNT}"
cd ../..

# Apply prod environment configuration
echo -e "${YELLOW}Applying prod environment configuration...${NC}"
cd environments/prod
terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="prefix=prod"
terraform apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="wif_provider=${WIF_PROVIDER}" \
  -var="service_account=${WIF_SERVICE_ACCOUNT}"

echo -e "${GREEN}=== Terraform Sequential Deployment Complete ===${NC}"
