#!/bin/bash
# check_required_apis.sh - Check and enable required APIs for MCP server deployment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_ID="cherry-ai-project"

echo -e "${BLUE}=== Checking Required APIs for MCP Server Deployment ===${NC}"
echo -e "Project ID: ${PROJECT_ID}"
echo

# Function to check if an API is enabled
check_api() {
  local api_name=$1
  local display_name=$2
  
  echo -e "${YELLOW}Checking if ${display_name} (${api_name}) is enabled...${NC}"
  
  if gcloud services list --enabled --filter="name:${api_name}" --project="${PROJECT_ID}" | grep -q "${api_name}"; then
    echo -e "${GREEN}✓ ${display_name} is enabled${NC}"
    return 0
  else
    echo -e "${RED}✗ ${display_name} is not enabled${NC}"
    return 1
  fi
}

# Function to enable an API
enable_api() {
  local api_name=$1
  local display_name=$2
  
  echo -e "${YELLOW}Enabling ${display_name} (${api_name})...${NC}"
  
  if gcloud services enable "${api_name}" --project="${PROJECT_ID}"; then
    echo -e "${GREEN}✓ ${display_name} enabled successfully${NC}"
    return 0
  else
    echo -e "${RED}✗ Failed to enable ${display_name}${NC}"
    return 1
  fi
}

# List of required APIs
declare -A APIS=(
  ["sts.googleapis.com"]="Security Token Service API"
  ["run.googleapis.com"]="Cloud Run API"
  ["containerregistry.googleapis.com"]="Container Registry API"
  ["cloudbuild.googleapis.com"]="Cloud Build API"
  ["artifactregistry.googleapis.com"]="Artifact Registry API"
  ["iam.googleapis.com"]="Identity and Access Management (IAM) API"
)

# Check and enable each API
for api_name in "${!APIS[@]}"; do
  display_name="${APIS[$api_name]}"
  
  if ! check_api "$api_name" "$display_name"; then
    echo -e "  Would you like to enable ${display_name}? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
      enable_api "$api_name" "$display_name"
    else
      echo -e "${YELLOW}⚠ Skipping ${display_name}${NC}"
    fi
  fi
  
  echo
done

echo -e "${BLUE}=== API Check Complete ===${NC}"
echo -e "All required APIs have been checked. Make sure all required APIs are enabled before deploying the MCP server."
echo -e "To deploy the MCP server, run:"
echo -e "  ./deploy_mcp_server.sh"