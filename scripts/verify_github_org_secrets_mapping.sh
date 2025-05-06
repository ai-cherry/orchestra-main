#!/bin/bash
# Script to verify GitHub organization secrets are properly mapped to .env file
# This script checks if the expected environment variables are set and have valid values

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENV_FILE=".env"

echo -e "${BLUE}=== GitHub Organization Secrets Mapping Verification ===${NC}"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE file not found.${NC}"
    echo "Please run './scripts/update_github_org_secrets.sh' first to create the mapping."
    exit 1
fi

# Define expected environment variables from GitHub org secrets
declare -a EXPECTED_VARS=(
    "GCP_SA_KEY_JSON"
    "GCP_PROJECT_ID"
    "GCP_SERVICE_ACCOUNT_KEY"
    "GCP_LOCATION"
    "GKE_CLUSTER_PROD"
    "GKE_CLUSTER_STAGING"
    "REDIS_HOST"
    "REDIS_PORT"
    "REDIS_PASSWORD"
)

# Function to check if variable exists in .env
check_env_var() {
    local var_name=$1
    
    if grep -q "^${var_name}=" "$ENV_FILE"; then
        local var_value=$(grep "^${var_name}=" "$ENV_FILE" | cut -d '=' -f2-)
        
        # Check if value is a placeholder or empty
        if [[ $var_value == *"<Set value from GitHub organization secret"* ]]; then
            echo -e "${YELLOW}⚠️  $var_name is mapped but contains a placeholder value${NC}"
            return 1
        elif [ -z "$var_value" ]; then
            echo -e "${RED}❌ $var_name is set but has an empty value${NC}"
            return 1
        else
            echo -e "${GREEN}✅ $var_name is properly mapped and has a value set${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ $var_name is not mapped in $ENV_FILE${NC}"
        return 1
    fi
}

# Print header
echo -e "\n${BLUE}Checking mapping of GitHub organization secrets to environment variables:${NC}\n"

# Check each expected variable
TOTAL_COUNT=${#EXPECTED_VARS[@]}
MAPPED_COUNT=0
PLACEHOLDER_COUNT=0
MISSING_COUNT=0

for var in "${EXPECTED_VARS[@]}"; do
    if check_env_var "$var"; then
        MAPPED_COUNT=$((MAPPED_COUNT + 1))
    elif grep -q "^${var}=.*<Set value from GitHub organization secret" "$ENV_FILE"; then
        PLACEHOLDER_COUNT=$((PLACEHOLDER_COUNT + 1))
    else
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

# Print summary
echo -e "\n${BLUE}=== Summary ===${NC}"
echo -e "Total variables checked: $TOTAL_COUNT"
echo -e "${GREEN}Properly mapped: $MAPPED_COUNT${NC}"
echo -e "${YELLOW}Mapped but with placeholders: $PLACEHOLDER_COUNT${NC}"
echo -e "${RED}Missing or empty: $MISSING_COUNT${NC}"

# Provide next steps
if [ $MISSING_COUNT -gt 0 ]; then
    echo -e "\n${YELLOW}Some variables are missing. Please run:${NC}"
    echo -e "  ./scripts/update_github_org_secrets.sh"
    echo -e "to map GitHub organization secrets to your .env file."
fi

if [ $PLACEHOLDER_COUNT -gt 0 ]; then
    echo -e "\n${YELLOW}Some variables have placeholder values. Please edit your $ENV_FILE file to set actual values.${NC}"
    echo -e "GitHub encryption prevents retrieving actual secret values, so you need to get them from a secure location."
fi

if [ $MAPPED_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "\n${GREEN}All GitHub organization secrets are properly mapped!${NC}"
else
    echo -e "\n${YELLOW}For more information, see:${NC}"
    echo -e "  docs/github_org_secrets_mapping.md"
fi

exit 0
