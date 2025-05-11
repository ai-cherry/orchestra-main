#!/bin/bash
# verify_github_secrets.sh - Script to verify GitHub organization secrets are accessible
# This script checks if the required GitHub organization secrets are available and accessible

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Load the centralized GitHub authentication utility
if [ -f "github_auth.sh" ]; then
    source github_auth.sh
else
    echo -e "${RED}Error: github_auth.sh not found. Please make sure it exists in the current directory.${NC}"
    exit 1
fi

# Configuration with fallbacks
GITHUB_ORG="${GITHUB_ORG:-ai-cherry}"

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   GITHUB ORGANIZATION SECRETS VERIFICATION   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Get GitHub token
GITHUB_TOKEN=$(get_github_token)

# Authenticate with GitHub
authenticate_github "$GITHUB_TOKEN"

# Function to check if a secret exists
check_secret() {
    local secret_name=$1
    local required=$2
    
    echo -e "${YELLOW}Checking for secret: ${secret_name}...${NC}"
    
    # Use GitHub API to check if the secret exists
    response=$(gh api "/orgs/${GITHUB_ORG}/actions/secrets/${secret_name}" 2>/dev/null || echo '{"message": "Not Found"}')
    
    if echo "$response" | grep -q "Not Found"; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ Required secret ${secret_name} not found${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️ Optional secret ${secret_name} not found${NC}"
            return 0
        fi
    else
        echo -e "${GREEN}✓ Secret ${secret_name} found${NC}"
        return 0
    fi
}

# Function to check if a variable exists
check_variable() {
    local var_name=$1
    local required=$2
    
    echo -e "${YELLOW}Checking for variable: ${var_name}...${NC}"
    
    # Use GitHub API to check if the variable exists
    response=$(gh api "/orgs/${GITHUB_ORG}/actions/variables/${var_name}" 2>/dev/null || echo '{"message": "Not Found"}')
    
    if echo "$response" | grep -q "Not Found"; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ Required variable ${var_name} not found${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️ Optional variable ${var_name} not found${NC}"
            return 0
        fi
    else
        value=$(echo "$response" | jq -r '.value')
        echo -e "${GREEN}✓ Variable ${var_name} found with value: ${value}${NC}"
        return 0
    fi
}

# Check for required secrets
echo -e "\n${BLUE}${BOLD}Checking required GitHub organization secrets...${NC}"
required_secrets=(
    "GH_CLASSIC_PAT_TOKEN"
    "GH_FINE_GRAINED_TOKEN"
    "GCP_PROJECT_ID"
    "GCP_REGION"
    "GCP_WORKLOAD_IDENTITY_PROVIDER"
    "GCP_SERVICE_ACCOUNT"
)

missing_required=0
for secret in "${required_secrets[@]}"; do
    if ! check_secret "$secret" "true"; then
        missing_required=$((missing_required + 1))
    fi
done

# Check for optional secrets
echo -e "\n${BLUE}${BOLD}Checking optional GitHub organization secrets...${NC}"
optional_secrets=(
    "VERTEX_AI_BADASS_KEY"
    "GEMINI_API_BADASS_KEY"
    "GEMINI_CODE_ASSIST_BADASS_KEY"
    "GEMINI_CLOUD_ASSIST_BADASS_KEY"
    "GCP_SECRET_SYNC_KEY"
    "VERTEX_SERVICE_ACCOUNT_EMAIL"
    "GEMINI_SERVICE_ACCOUNT_EMAIL"
)

missing_optional=0
for secret in "${optional_secrets[@]}"; do
    if ! check_secret "$secret" "false"; then
        missing_optional=$((missing_optional + 1))
    fi
done

# Check for required variables
echo -e "\n${BLUE}${BOLD}Checking required GitHub organization variables...${NC}"
required_variables=(
    "GCP_PROJECT_ID"
    "GCP_REGION"
)

for var in "${required_variables[@]}"; do
    check_variable "$var" "true"
done

# Check for optional variables
echo -e "\n${BLUE}${BOLD}Checking optional GitHub organization variables...${NC}"
optional_variables=(
    "GCP_PROJECT_NAME"
    "GCP_ZONE"
    "DEPLOYMENT_ENVIRONMENT"
)

for var in "${optional_variables[@]}"; do
    check_variable "$var" "false"
done

# Print summary
echo -e "\n${BLUE}${BOLD}Summary:${NC}"
echo -e "Required secrets: ${GREEN}$((${#required_secrets[@]} - $missing_required))${NC}/${#required_secrets[@]} found"
echo -e "Optional secrets: ${GREEN}$((${#optional_secrets[@]} - $missing_optional))${NC}/${#optional_secrets[@]} found"

if [ $missing_required -gt 0 ]; then
    echo -e "\n${RED}${BOLD}Warning: Some required secrets are missing!${NC}"
    echo -e "Please set up the missing required secrets before deploying."
    echo -e "You can use the setup_github_secrets.sh script to set up the required secrets."
    exit 1
else
    echo -e "\n${GREEN}${BOLD}All required secrets are available!${NC}"
    echo -e "You can now proceed with deployment."
fi