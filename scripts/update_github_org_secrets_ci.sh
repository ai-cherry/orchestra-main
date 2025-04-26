#!/bin/bash
# Non-interactive script for CI/CD environments to map GitHub organization secrets to .env file
# This script requires the GitHub CLI (gh) to be installed and authenticated

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability in logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENV_FILE=".env"
BACKUP_FILE=".env.backup.$(date +%Y%m%d%H%M%S)"

# Parse command line arguments
ORG_NAME=""
AUTO_YES=false

print_usage() {
  echo "Usage: $0 --org <github-org-name> [--yes] [--env-file <path>]"
  echo ""
  echo "Options:"
  echo "  --org        GitHub organization name (required)"
  echo "  --yes        Automatically confirm all prompts (for CI/CD)"
  echo "  --env-file   Path to .env file (default: .env in current directory)"
  echo ""
  echo "Example:"
  echo "  $0 --org my-github-org --yes"
}

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --org) ORG_NAME="$2"; shift ;;
    --yes) AUTO_YES=true ;;
    --env-file) ENV_FILE="$2"; shift ;;
    --help) print_usage; exit 0 ;;
    *) echo "Unknown parameter: $1"; print_usage; exit 1 ;;
  esac
  shift
done

# Validate required parameters
if [ -z "$ORG_NAME" ]; then
  echo -e "${RED}Error: GitHub organization name is required${NC}"
  print_usage
  exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
  echo "Please install it: https://cli.github.com/manual/installation"
  exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
  echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
  echo "Please run: gh auth login"
  exit 1
fi

echo -e "${BLUE}Running in CI/CD mode with auto-confirmation: $AUTO_YES${NC}"
echo -e "${BLUE}Using environment file: $ENV_FILE${NC}"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}Warning: $ENV_FILE file not found. Creating a new one.${NC}"
  touch "$ENV_FILE"
fi

# Create a backup of the current .env file
cp "$ENV_FILE" "$BACKUP_FILE"
echo -e "${BLUE}Created backup of $ENV_FILE as $BACKUP_FILE${NC}"

echo -e "${GREEN}Fetching organization secrets for: $ORG_NAME${NC}"

# Map of GitHub organization secrets to .env variables
# Format: GitHub_Secret_Name:Env_Variable_Name
declare -A SECRET_MAPPING=(
  ["ORG_GCP_CREDENTIALS"]="GCP_SA_KEY_JSON"
  ["ORG_GCP_PROJECT_ID"]="GCP_PROJECT_ID"
  ["ORG_GCP_PROJECT_NUMBER"]="GCP_PROJECT_NUMBER"
  ["ORG_VERTEX_KEY"]="VERTEX_KEY"
  ["ORG_GCP_SERVICE_ACCOUNT_KEY"]="GCP_SERVICE_ACCOUNT_KEY"
  ["ORG_GCP_REGION"]="GCP_LOCATION"
  ["ORG_GKE_CLUSTER_PROD"]="GKE_CLUSTER_PROD"
  ["ORG_GKE_CLUSTER_STAGING"]="GKE_CLUSTER_STAGING"
  ["ORG_PORTKEY_API_KEY"]="PORTKEY_API_KEY"
  ["ORG_TERRAFORM_API_KEY"]="TERRAFORM_API_KEY"
  ["ORG_TERRAFORM_ORGANIZATION_TOKEN"]="TERRAFORM_ORGANIZATION_TOKEN"
  ["ORG_REDIS_HOST"]="REDIS_HOST"
  ["ORG_REDIS_PORT"]="REDIS_PORT"
  ["ORG_REDIS_USER"]="REDIS_USER"
  ["ORG_REDIS_PASSWORD"]="REDIS_PASSWORD"
  ["ORG_REDIS_DATABASE_NAME"]="REDIS_DATABASE_NAME"
  ["ORG_REDIS_DATABASE_ENDPOINT"]="REDIS_DATABASE_ENDPOINT"
)

# Function to update .env file with a key-value pair
update_env_file() {
  local key=$1
  local value=$2
  local file=$3

  # Escape special characters in the value for sed
  value=$(echo "$value" | sed 's/[\/&]/\\&/g')
  
  # Check if the key already exists in the file
  if grep -q "^${key}=" "$file"; then
    # Update existing key
    sed -i "s/^${key}=.*/${key}=${value}/" "$file"
  else
    # Add new key
    echo "${key}=${value}" >> "$file"
  fi
}

# Check if organization is accessible
if ! gh api "orgs/$ORG_NAME" &> /dev/null; then
  echo -e "${RED}Error: Cannot access organization '$ORG_NAME'${NC}"
  echo "Please check if you have the correct organization name and sufficient permissions"
  exit 1
fi

# Get list of organization secrets (this only works if you have admin access)
SECRETS_RESPONSE=$(gh api "orgs/$ORG_NAME/actions/secrets" 2>/dev/null || echo '{"secrets":[]}')
SECRETS_COUNT=$(echo "$SECRETS_RESPONSE" | jq -r '.total_count // 0')

if [ "$SECRETS_COUNT" -eq 0 ]; then
  echo -e "${RED}Error: No secrets found or insufficient permissions${NC}"
  echo "You might not have admin permissions to access organization secrets"
  exit 1
fi

echo -e "${GREEN}Found $SECRETS_COUNT organization secrets${NC}"

# Extract secret names
SECRET_NAMES=$(echo "$SECRETS_RESPONSE" | jq -r '.secrets[].name')

UPDATED_COUNT=0
NOT_FOUND_COUNT=0
NOT_MAPPED_COUNT=0

# Display the secrets that will be mapped
echo -e "\n${BLUE}The following secrets will be mapped:${NC}"
for SECRET_NAME in $SECRET_NAMES; do
  ENV_VAR=${SECRET_MAPPING[$SECRET_NAME]}
  if [ ! -z "$ENV_VAR" ]; then
    echo "  $SECRET_NAME → $ENV_VAR"
  fi
done

# Process each secret mapping
for SECRET_NAME in $SECRET_NAMES; do
  ENV_VAR=${SECRET_MAPPING[$SECRET_NAME]}
  
  if [ ! -z "$ENV_VAR" ]; then
    # For actual implementation, you would fetch the secret value through another secure method
    # Since GitHub encrypts these values, we're just adding placeholder text
    PLACEHOLDER="<Set value from GitHub organization secret: $SECRET_NAME>"
    
    echo -e "Mapping ${BLUE}$SECRET_NAME${NC} to ${GREEN}$ENV_VAR${NC}"
    update_env_file "$ENV_VAR" "$PLACEHOLDER" "$ENV_FILE"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
  else
    echo -e "${YELLOW}No mapping defined for GitHub secret: $SECRET_NAME${NC}"
    NOT_MAPPED_COUNT=$((NOT_MAPPED_COUNT + 1))
  fi
done

# Check for mapped env vars that don't have corresponding GitHub secrets
for GH_SECRET in "${!SECRET_MAPPING[@]}"; do
  ENV_VAR=${SECRET_MAPPING[$GH_SECRET]}
  
  if ! echo "$SECRET_NAMES" | grep -q "$GH_SECRET"; then
    echo -e "${RED}GitHub secret not found: $GH_SECRET (would map to $ENV_VAR)${NC}"
    NOT_FOUND_COUNT=$((NOT_FOUND_COUNT + 1))
  fi
done

# Write a summary to output
echo -e "\n${GREEN}Mapping complete!${NC}"
echo -e "Updated: $UPDATED_COUNT secrets"
echo -e "Not mapped: $NOT_MAPPED_COUNT secrets (no mapping defined)"
echo -e "Not found: $NOT_FOUND_COUNT secrets (defined in mapping but not found in GitHub)"

echo -e "\n${YELLOW}IMPORTANT: The .env file has been updated with placeholder values.${NC}"
echo -e "${YELLOW}You need to set the actual secret values from your secure storage location.${NC}"
echo -e "${YELLOW}A backup of your original .env file was created at: $BACKUP_FILE${NC}"

if [ $NOT_FOUND_COUNT -gt 0 ]; then
  echo -e "\n${YELLOW}Warning: Some expected GitHub organization secrets were not found.${NC}"
  
  if [ "$AUTO_YES" = true ]; then
    # In CI/CD mode, we might want to exit with a warning but not a hard error
    echo -e "${YELLOW}Continuing despite missing secrets (auto-confirmation mode)${NC}"
  fi
fi

echo -e "\n${GREEN}GitHub organization secrets mapping completed!${NC}"
exit 0
