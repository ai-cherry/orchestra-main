#!/bin/bash
# Master script to handle the complete GCP infrastructure deployment process
# 1. Create service account keys with extensive permissions
# 2. Update GitHub secrets
# 3. Apply Terraform in sequence (common -> dev -> prod)
# 4. Switch to Workload Identity Federation for improved security

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   COMPLETE GCP INFRASTRUCTURE DEPLOYMENT PROCESS   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# Function to check if a script exists and is executable
check_script() {
  local script_name=$1
  
  if [ ! -f "$script_name" ]; then
    echo -e "${RED}Error: Script $script_name not found.${NC}"
    exit 1
  fi
  
  if [ ! -x "$script_name" ]; then
    echo -e "${YELLOW}Warning: Script $script_name is not executable. Making it executable...${NC}"
    chmod +x "$script_name"
  fi
}

# Function to prompt for confirmation
confirm() {
  local message=$1
  local response
  
  echo -e "${YELLOW}${message} (y/n)${NC}"
  read -r response
  
  if [[ "$response" =~ ^[Yy]$ ]]; then
    return 0  # true
  else
    return 1  # false
  fi
}

# Check if all required scripts exist
echo -e "${YELLOW}Checking required scripts...${NC}"
check_script "create_badass_service_keys.sh"
check_script "apply_terraform_sequence.sh"
check_script "switch_to_wif_authentication.sh"
check_script "secure_service_key_creation.sh"
echo -e "${GREEN}All required scripts are available.${NC}"

# Display the process overview
echo -e "\n${YELLOW}${BOLD}DEPLOYMENT PROCESS OVERVIEW:${NC}"
echo -e "${YELLOW}1. Create service account keys with extensive permissions${NC}"
echo -e "${YELLOW}2. Apply Terraform configurations in sequence (common -> dev -> prod)${NC}"
echo -e "${YELLOW}3. Switch to Workload Identity Federation for improved security${NC}"

# Confirm to proceed
if confirm "Do you want to proceed with the complete deployment process?"; then
  echo -e "\n${GREEN}Starting deployment process...${NC}"
else
  echo -e "\n${RED}Deployment cancelled.${NC}"
  exit 0
fi

# Step 1: Create service account keys
echo -e "\n${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   STEP 1: CREATE SERVICE ACCOUNT KEYS   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

if confirm "Do you want to create service account keys with extensive permissions?"; then
  ./secure_service_key_creation.sh
else
  echo -e "${YELLOW}Skipping service account key creation.${NC}"
fi

# Confirm GitHub secrets are updated
echo -e "\n${YELLOW}Ensure all GitHub secrets are updated with the service account keys before proceeding.${NC}"
if ! confirm "Have you updated the GitHub secrets with the service account keys?"; then
  echo -e "${RED}Please update GitHub secrets before proceeding with Terraform apply.${NC}"
  echo -e "${YELLOW}You can run this script again after updating the secrets.${NC}"
  exit 0
fi

# Step 2: Apply Terraform
echo -e "\n${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   STEP 2: APPLY TERRAFORM CONFIGURATIONS   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

if confirm "Do you want to apply Terraform configurations in sequence?"; then
  ./apply_terraform_sequence.sh
else
  echo -e "${YELLOW}Skipping Terraform apply.${NC}"
fi

# Confirm Terraform apply was successful
if ! confirm "Was the Terraform apply process successful?"; then
  echo -e "${RED}Please resolve Terraform apply issues before proceeding to WIF setup.${NC}"
  echo -e "${YELLOW}You can run this script again after resolving the issues.${NC}"
  exit 0
fi

# Step 3: Set up Workload Identity Federation
echo -e "\n${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   STEP 3: SET UP WORKLOAD IDENTITY FEDERATION   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

if confirm "Do you want to set up Workload Identity Federation for improved security?"; then
  # First, set up the WIF infrastructure in GCP
  check_script "secure_setup_workload_identity.sh"
  ./secure_setup_workload_identity.sh
  
  # Then, update the GitHub workflow files to use WIF
  if confirm "Do you want to update GitHub workflow files to use Workload Identity Federation?"; then
    ./switch_to_wif_authentication.sh
  else
    echo -e "${YELLOW}Skipping GitHub workflow updates.${NC}"
    echo -e "${YELLOW}You can run ./switch_to_wif_authentication.sh later to update workflows.${NC}"
  fi
else
  echo -e "${YELLOW}Skipping Workload Identity Federation setup.${NC}"
  echo -e "${RED}WARNING: Using service account keys long-term is not recommended for security reasons.${NC}"
  echo -e "${RED}Please set up Workload Identity Federation as soon as possible.${NC}"
fi

# Completion message
echo -e "\n${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}   DEPLOYMENT PROCESS COMPLETED   ${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Verify the deployed infrastructure is working as expected"
echo -e "2. If you've switched to WIF, update your GitHub workflows to use WIF authentication"
echo -e "3. Delete any local copies of service account keys for security"
echo -e "4. Refer to GCP_TERRAFORM_DEPLOYMENT_GUIDE.md for detailed documentation"

echo -e "\n${GREEN}Thank you for using the GCP infrastructure deployment script!${NC}"
