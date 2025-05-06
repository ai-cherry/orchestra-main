#!/bin/bash
# Test script to validate Terraform plans for both environments
# This script runs terraform plan on both dev and prod environments to verify configurations

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running Terraform validation tests...${NC}"

# Test dev environment
echo -e "\n${YELLOW}Testing dev environment...${NC}"
cd "$(dirname "$0")/dev"
terraform init -backend=false
terraform validate
terraform plan -var="env=dev" -out=dev.tfplan -lock=false -refresh=false
echo -e "${GREEN}Dev environment plan successful!${NC}"

# Test prod environment
echo -e "\n${YELLOW}Testing prod environment...${NC}"
cd ../prod
terraform init -backend=false
terraform validate
terraform plan -var="env=prod" -out=prod.tfplan -lock=false -refresh=false
echo -e "${GREEN}Prod environment plan successful!${NC}"

# Clean up plan files
cd ../dev
rm -f dev.tfplan
cd ../prod
rm -f prod.tfplan

echo -e "\n${GREEN}All environment configurations validated successfully!${NC}"
echo -e "${YELLOW}Note: This was a dry run with no state or backend configuration.${NC}"
echo -e "${YELLOW}To apply these configurations, follow the steps in docs/infra.md${NC}"
