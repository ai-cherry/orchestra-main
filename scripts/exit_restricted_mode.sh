#!/bin/bash
# exit_restricted_mode.sh
# Script to detect and exit restricted mode in GitHub Codespaces
# This ensures Terraform scripts can run properly with full access to resources

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== AI Orchestra Restricted Mode Detection ===${NC}"

# Check if we're in a GitHub Codespace
if [ -z "${CODESPACES}" ]; then
  echo -e "${YELLOW}Not running in GitHub Codespaces, skipping restricted mode check${NC}"
  exit 0
fi

# Check for signs of restricted mode
RESTRICTED_MODE=false

# Check if standard environment variables are missing
if [ -z "${GITHUB_TOKEN}" ]; then
  echo -e "${RED}GITHUB_TOKEN is not set - possible indicator of restricted mode${NC}"
  RESTRICTED_MODE=true
fi

# Check if we can access certain resources
if ! gcloud auth list &>/dev/null; then
  echo -e "${RED}Unable to access gcloud auth - possible indicator of restricted mode${NC}"
  RESTRICTED_MODE=true
fi

if ! terraform version &>/dev/null; then
  echo -e "${RED}Unable to access terraform - possible indicator of restricted mode${NC}"
  RESTRICTED_MODE=true
fi

# If in restricted mode, attempt to exit
if [ "$RESTRICTED_MODE" = true ]; then
  echo -e "${YELLOW}Detected restricted mode, attempting to exit...${NC}"
  
  # Execute commands to exit restricted mode
  if [ -f "./force_standard_mode.py" ]; then
    echo -e "${YELLOW}Running force_standard_mode.py...${NC}"
    python ./force_standard_mode.py
  elif [ -f "./exit_restricted_mode.sh" ]; then
    echo -e "${YELLOW}Running existing exit_restricted_mode.sh...${NC}"
    bash ./exit_restricted_mode.sh
  elif [ -f "./force_to_standard_mode.sh" ]; then
    echo -e "${YELLOW}Running force_to_standard_mode.sh...${NC}"
    bash ./force_to_standard_mode.sh
  else
    echo -e "${RED}No existing scripts found to exit restricted mode${NC}"
    echo -e "${YELLOW}Please run one of the following commands manually:${NC}"
    echo -e "  - python ./force_standard_mode.py"
    echo -e "  - bash ./exit_restricted_mode.sh"
    echo -e "  - bash ./force_to_standard_mode.sh"
    exit 1
  fi
  
  echo -e "${GREEN}Attempted to exit restricted mode. Please restart your terminal session.${NC}"
  echo -e "${YELLOW}After restarting, run this script again to verify standard mode.${NC}"
else
  echo -e "${GREEN}Not in restricted mode, proceeding with normal operation.${NC}"
fi

echo -e "${GREEN}=== Restricted Mode Check Complete ===${NC}"
exit 0