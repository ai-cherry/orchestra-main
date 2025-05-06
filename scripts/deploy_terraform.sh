#!/bin/bash
# deploy_terraform.sh
# Script to deploy Terraform configurations for AI Orchestra project
# Automates the process of planning and applying Terraform for dev and prod environments

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

echo -e "${YELLOW}=== AI Orchestra Terraform Deployment ===${NC}"
echo -e "${YELLOW}Running from:${NC} $(pwd)"

# Function to deploy a specific environment
deploy_environment() {
  local env=$1
  local project_id=${2:-"cherry-ai-project"}
  
  echo -e "\n${YELLOW}=== Deploying $env environment ===${NC}"
  
  # Navigate to environment directory
  cd "$PROJECT_ROOT/infra/terraform/gcp/environments/$env"
  
  # Run terraform plan
  echo -e "${YELLOW}Running terraform plan for $env...${NC}"
  terraform plan -var="project_id=$project_id"
  
  # Confirm before applying
  if [ "$AUTO_APPROVE" != "true" ]; then
    read -p "Do you want to apply these changes to $env? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${YELLOW}Skipping apply for $env environment${NC}"
      cd "$PROJECT_ROOT"
      return
    fi
  fi
  
  # Apply terraform changes
  echo -e "${YELLOW}Applying terraform changes for $env...${NC}"
  terraform apply -var="project_id=$project_id" ${AUTO_APPROVE:+-auto-approve}
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully deployed $env environment${NC}"
  else
    echo -e "${RED}✗ Failed to deploy $env environment${NC}"
    cd "$PROJECT_ROOT"
    exit 1
  fi
  
  # Return to project root
  cd "$PROJECT_ROOT"
}

# Parse command line arguments
PROJECT_ID="cherry-ai-project"
AUTO_APPROVE=false
ENVIRONMENTS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id=*)
      PROJECT_ID="${1#*=}"
      shift
      ;;
    --auto-approve)
      AUTO_APPROVE=true
      shift
      ;;
    --env=*)
      ENVIRONMENTS+=("${1#*=}")
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# If no environments specified, deploy both dev and prod
if [ ${#ENVIRONMENTS[@]} -eq 0 ]; then
  ENVIRONMENTS=("dev" "prod")
fi

# Deploy each environment
for env in "${ENVIRONMENTS[@]}"; do
  deploy_environment "$env" "$PROJECT_ID"
done

echo -e "\n${GREEN}=== Terraform deployment completed ===${NC}"
exit 0