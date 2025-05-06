#!/bin/bash
# validate_terraform.sh
# Script to validate Terraform configurations for AI Orchestra project
# - Formats all Terraform files in the infra directory
# - Initializes and validates each environment directory

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root directory (assuming script is run from project root or scripts directory)
if [[ $(basename $(pwd)) == "scripts" ]]; then
  PROJECT_ROOT="$(pwd)/.."
else
  PROJECT_ROOT="$(pwd)"
fi

# Ensure we're in the project root
cd "$PROJECT_ROOT"

echo -e "${YELLOW}=== AI Orchestra Terraform Validation ===${NC}"
echo -e "${YELLOW}Running from:${NC} $(pwd)"

# Step 1: Format all Terraform files
echo -e "\n${YELLOW}=== Formatting Terraform files ===${NC}"
terraform fmt -recursive ./infra
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Terraform formatting completed successfully${NC}"
else
  echo -e "${RED}✗ Terraform formatting failed${NC}"
  exit 1
fi

# Step 2: Initialize and validate each environment
ENVIRONMENTS=("common" "dev" "prod")
INFRA_PATH="./infra/terraform/gcp/environments"

for env in "${ENVIRONMENTS[@]}"; do
  ENV_PATH="$INFRA_PATH/$env"
  
  # Check if environment directory exists
  if [ ! -d "$ENV_PATH" ]; then
    echo -e "${YELLOW}⚠ Environment directory not found: $ENV_PATH - skipping${NC}"
    continue
  fi
  
  echo -e "\n${YELLOW}=== Validating $env environment ===${NC}"
  
  # Navigate to environment directory
  cd "$ENV_PATH"
  
  # Initialize Terraform with upgrade flag
  echo -e "${YELLOW}Initializing Terraform for $env...${NC}"
  terraform init -upgrade
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Terraform initialization failed for $env${NC}"
    cd "$PROJECT_ROOT"
    exit 1
  fi
  
  # Validate Terraform configuration
  echo -e "${YELLOW}Validating Terraform configuration for $env...${NC}"
  terraform validate
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Terraform validation successful for $env${NC}"
  else
    echo -e "${RED}✗ Terraform validation failed for $env${NC}"
    cd "$PROJECT_ROOT"
    exit 1
  fi
  
  # Return to project root
  cd "$PROJECT_ROOT"
done

echo -e "\n${GREEN}=== All Terraform validations completed successfully ===${NC}"
exit 0