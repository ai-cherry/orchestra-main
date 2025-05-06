#!/bin/bash
# Secure wrapper script to set environment variables and run the service key creation script
# This version does NOT hardcode sensitive credentials

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   SECURE SERVICE KEY CREATION SCRIPT WRAPPER   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

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
  
  echo -e "${GREEN}Script $script_name is ready to run.${NC}"
}

# Securely get GitHub PAT
get_github_pat() {
  # Check if PAT is provided as environment variable
  if [ -n "$GITHUB_PAT" ]; then
    echo -e "${GREEN}Using GitHub PAT from environment variable.${NC}"
    return 0
  fi
  
  # Prompt the user for the PAT
  echo -e "${YELLOW}GitHub Personal Access Token not found in environment.${NC}"
  echo -e "${YELLOW}Please enter your GitHub PAT (input will be hidden):${NC}"
  read -s GITHUB_PAT
  
  if [ -z "$GITHUB_PAT" ]; then
    echo -e "${RED}Error: GitHub Personal Access Token not provided.${NC}"
    exit 1
  fi
  
  # Export so it's available to the called script
  export GITHUB_PAT
  echo -e "${GREEN}GitHub PAT received.${NC}"
}

# Main function
main() {
  echo -e "${YELLOW}Starting secure service key creation process...${NC}"
  
  # Check if the required scripts exist and are executable
  check_script "create_badass_service_keys.sh"
  
  # Get the GitHub PAT securely
  get_github_pat
  
  echo -e "\n${YELLOW}Running service key creation script...${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  # Run the service key creation script
  ./create_badass_service_keys.sh
  
  echo -e "${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}Service key creation completed.${NC}"
  
  echo -e "\n${YELLOW}Next steps:${NC}"
  echo -e "1. Update GitHub secrets using the instructions from the script output"
  echo -e "2. Run the apply_terraform_sequence.sh script to apply Terraform configurations"
  echo -e "3. After Terraform apply, run switch_to_wif_authentication.sh to switch to WIF"
}

# Execute the main function
main
