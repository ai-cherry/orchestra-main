#!/bin/bash
# Secret Manager Validation Script
# This script runs the secret validation tests for different environments

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Make the validation script executable
chmod +x validate_secrets.py

# Check for dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Error: python3 not found${NC}"
  exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null; then
  if ! command -v pip &> /dev/null; then
    echo -e "${YELLOW}Installing pip...${NC}"
    # Try to install pip using apt-get (for Debian/Ubuntu)
    if command -v apt-get &> /dev/null; then
      sudo apt-get update && sudo apt-get install -y python3-pip
    else
      echo -e "${RED}Error: pip not found and could not be installed automatically${NC}"
      echo -e "Please install pip manually with:"
      echo -e "  - Debian/Ubuntu: sudo apt-get install python3-pip"
      echo -e "  - RHEL/CentOS/Fedora: sudo dnf install python3-pip"
      exit 1
    fi
  fi
fi

# Determine which pip command to use
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
  PIP_CMD="pip"
fi

# Check for pip packages
echo -e "${YELLOW}Checking for required Python packages...${NC}"
if ! python3 -c "import google.cloud.secretmanager" &> /dev/null; then
  echo -e "${YELLOW}Installing google-cloud-secretmanager...${NC}"
  $PIP_CMD install --user google-cloud-secretmanager
fi

# Check GCP authentication
echo -e "${YELLOW}Checking GCP authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q '@'; then
  echo -e "${RED}Error: Not authenticated with gcloud${NC}"
  echo "Please run: gcloud auth login"
  exit 1
fi

# Function to validate a specific environment
validate_env() {
  local env=$1
  local project_id=$2
  local service_name=$3

  echo -e "\n${GREEN}===============================================${NC}"
  echo -e "${GREEN}Validating ${env} environment in project ${project_id}${NC}"
  echo -e "${GREEN}===============================================${NC}"

  # Run the validation script
  python3 validate_secrets.py --env ${env} --project-id ${project_id} --service ${service_name}
  local result=$?

  if [ $result -eq 0 ]; then
    echo -e "${GREEN}✅ ${env} environment validation successful!${NC}"
  else
    echo -e "${RED}❌ ${env} environment validation failed!${NC}"
  fi

  return $result
}

# Get parameters
PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
ENV=${2:-"dev"}
SERVICE=${3:-"orchestra-api"}

if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}Error: Project ID not provided and could not be determined automatically${NC}"
  echo "Usage: $0 [project-id] [environment] [service-name]"
  exit 1
fi

# Validate the specified environment
validate_env $ENV $PROJECT_ID $SERVICE

echo -e "\n${GREEN}Validation complete!${NC}"