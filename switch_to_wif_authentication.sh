#!/bin/bash
# Script to update GitHub Actions workflows to use Workload Identity Federation
# instead of service account keys after initial Terraform apply

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
WORKFLOW_FILE="github_actions_migration_workflow.yml"
WIF_PROVIDER_FILE="/tmp/wif_provider.txt"
SERVICE_ACCOUNT_FILE="/tmp/service_account.txt"

# Print header
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   SWITCH GITHUB ACTIONS TO WORKLOAD IDENTITY FEDERATION   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# Check if WIF values are available
if [[ ! -f "$WIF_PROVIDER_FILE" || ! -f "$SERVICE_ACCOUNT_FILE" ]]; then
  echo -e "${YELLOW}WIF values not found in tmp files. Checking for values in environment...${NC}"
  
  # If not available in files, try to get from environment
  if [[ -z "$WIF_PROVIDER" || -z "$SERVICE_ACCOUNT" ]]; then
    echo -e "${RED}Error: WIF provider and service account values not found.${NC}"
    echo -e "${YELLOW}You need to run Terraform to get these values or provide them manually.${NC}"
    
    # Prompt for manual entry
    read -p "Enter WIF provider ID: " WIF_PROVIDER
    read -p "Enter service account email: " SERVICE_ACCOUNT
    
    if [[ -z "$WIF_PROVIDER" || -z "$SERVICE_ACCOUNT" ]]; then
      echo -e "${RED}Error: Required values not provided. Exiting.${NC}"
      exit 1
    fi
  fi
else
  # Read values from files
  WIF_PROVIDER=$(cat "$WIF_PROVIDER_FILE")
  SERVICE_ACCOUNT=$(cat "$SERVICE_ACCOUNT_FILE")
  
  echo -e "${GREEN}Found WIF values in temporary files:${NC}"
  echo -e "WIF Provider: $WIF_PROVIDER"
  echo -e "Service Account: $SERVICE_ACCOUNT"
fi

# Check if workflow file exists
if [[ ! -f "$WORKFLOW_FILE" ]]; then
  echo -e "${RED}Error: Workflow file '$WORKFLOW_FILE' not found.${NC}"
  exit 1
fi

echo -e "\n${YELLOW}Updating GitHub Actions workflow file to use WIF...${NC}"

# Create temporary file
TMP_FILE=$(mktemp)

# Process the file - uncomment WIF lines and comment out credentials_json line
cat "$WORKFLOW_FILE" | sed '/google-github-actions\/auth@v1/{
  n
  n
  s/^          # workload_identity_provider/          workload_identity_provider/
  n
  s/^          # service_account/          service_account/
  n
  s/^          credentials_json/          # credentials_json/
}' > "$TMP_FILE"

# Check if the sed command made changes
if diff -q "$WORKFLOW_FILE" "$TMP_FILE" > /dev/null; then
  echo -e "${RED}No changes were made to the file. Make sure the file format matches the expected pattern.${NC}"
  exit 1
fi

# Replace the original file
cp "$TMP_FILE" "$WORKFLOW_FILE"
rm "$TMP_FILE"

echo -e "${GREEN}Successfully updated workflow file to use Workload Identity Federation.${NC}"

# Instructions for updating GitHub secrets
echo -e "\n${BLUE}${BOLD}-----------------------------------------------------------------------${NC}"
echo -e "${YELLOW}${BOLD}Next Steps:${NC}"
echo -e "${BLUE}${BOLD}-----------------------------------------------------------------------${NC}"
echo -e "1. Update GitHub organization secrets with WIF values using GitHub CLI:"
echo -e "   ${GREEN}gh secret set WORKLOAD_IDENTITY_PROVIDER --org ai-cherry --body \"$WIF_PROVIDER\"${NC}"
echo -e "   ${GREEN}gh secret set SERVICE_ACCOUNT --org ai-cherry --body \"$SERVICE_ACCOUNT\"${NC}"
echo -e ""
echo -e "2. Commit and push the updated workflow file to GitHub:"
echo -e "   ${GREEN}git add $WORKFLOW_FILE${NC}"
echo -e "   ${GREEN}git commit -m \"Switch to Workload Identity Federation for GCP authentication\"${NC}"
echo -e "   ${GREEN}git push${NC}"
echo -e ""
echo -e "3. After confirming that WIF authentication works, consider removing the service account key secrets"
echo -e "   for improved security:"
echo -e "   ${GREEN}gh secret delete GCP_ADMIN_SA_KEY_JSON --org ai-cherry${NC}"
echo -e ""
echo -e "${YELLOW}${BOLD}Security Note:${NC}"
echo -e "Using Workload Identity Federation is more secure than storing service account keys in GitHub."
echo -e "It eliminates the risk of leaked credentials and follows GCP security best practices."

echo -e "\n${GREEN}${BOLD}Done!${NC}"
