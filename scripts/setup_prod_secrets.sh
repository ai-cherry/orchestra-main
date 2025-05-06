#!/bin/bash
# setup_prod_secrets.sh
#
# This script helps set up production secrets in Google Secret Manager.
# These secrets are used in the production environment for securing
# sensitive information like API keys, passwords, etc.
#
# Run this script with appropriate permissions to create and manage secrets.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}${BOLD}   Orchestra Production Secrets Setup   ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Default values
PROJECT_ID=${1:-"agi-baby-cherry"}  # Default project ID, can be overridden by first argument

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it and try again.${NC}"
    exit 1
fi

# Check authentication
echo -e "${YELLOW}Checking GCP authentication...${NC}"
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$ACCOUNT" ]; then
    echo -e "${RED}Error: Not authenticated to Google Cloud. Run 'gcloud auth login' and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}Authenticated as: $ACCOUNT${NC}"

# Set project
echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Check if Secret Manager API is enabled
echo -e "${YELLOW}Checking if Secret Manager API is enabled...${NC}"
if ! gcloud services list --enabled | grep -q "secretmanager.googleapis.com"; then
    echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
    gcloud services enable secretmanager.googleapis.com
fi

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local prompt=$2
    local default_value=$3
    
    echo -e "\n${BOLD}Setting up secret: ${secret_name}${NC}"
    
    # Check if the secret already exists
    if gcloud secrets describe $secret_name &> /dev/null; then
        echo -e "${YELLOW}Secret '$secret_name' already exists${NC}"
        read -p "Do you want to update it? (y/n, default: n): " update_secret
        
        if [ "$update_secret" != "y" ] && [ "$update_secret" != "Y" ]; then
            echo -e "${YELLOW}Skipping update of secret '$secret_name'${NC}"
            return
        fi
    else
        echo -e "${YELLOW}Creating new secret '$secret_name'${NC}"
        gcloud secrets create $secret_name --replication-policy="automatic"
    fi
    
    # Get the secret value from the user
    if [ -n "$default_value" ]; then
        prompt="$prompt (press Enter to use default)"
    fi
    
    # Use read -s for sensitive input (won't show on screen)
    echo -e "${YELLOW}$prompt${NC}"
    read -s secret_value
    echo ""  # Add newline since read -s doesn't add one
    
    # Use default if nothing entered
    if [ -z "$secret_value" ] && [ -n "$default_value" ]; then
        secret_value="$default_value"
        echo -e "${YELLOW}Using default value${NC}"
    fi
    
    # Add or update the secret value
    echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    
    echo -e "${GREEN}Secret '$secret_name' has been set${NC}"
}

# List of secrets to create/update
echo -e "\n${BOLD}Setting up production secrets...${NC}"

# OpenRouter API key
create_or_update_secret "openrouter-api-key-prod" "Enter your OpenRouter API key:" ""

# Portkey API key (if applicable)
read -p "Are you using Portkey? (y/n, default: n): " use_portkey
if [ "$use_portkey" == "y" ] || [ "$use_portkey" == "Y" ]; then
    create_or_update_secret "portkey-api-key-prod" "Enter your Portkey API key:" ""
fi

# PostgreSQL password for production
create_or_update_secret "postgres-password-prod" "Enter a strong PostgreSQL password:" $(openssl rand -base64 16)

# Redis password for production
create_or_update_secret "redis-password-prod" "Enter a strong Redis password:" $(openssl rand -base64 16)

# Figma integration (if applicable)
read -p "Are you using Figma integration? (y/n, default: n): " use_figma
if [ "$use_figma" == "y" ] || [ "$use_figma" == "Y" ]; then
    create_or_update_secret "figma-pat-prod" "Enter your Figma Personal Access Token:" ""
    create_or_update_secret "figma-webhook-secret-prod" "Enter a secret for Figma webhook verification:" $(openssl rand -base64 24)
fi

# Custom secrets
read -p "Do you want to add any custom secrets? (y/n, default: n): " add_custom
if [ "$add_custom" == "y" ] || [ "$add_custom" == "Y" ]; then
    while true; do
        echo -e "\n${BOLD}Adding custom secret${NC}"
        read -p "Enter secret name (or leave empty to finish): " custom_name
        
        if [ -z "$custom_name" ]; then
            break
        fi
        
        # Add proper suffix if not already present
        if [[ ! "$custom_name" == *-prod ]]; then
            custom_name="$custom_name-prod"
            echo -e "${YELLOW}Adding '-prod' suffix: $custom_name${NC}"
        fi
        
        create_or_update_secret "$custom_name" "Enter value for $custom_name:" ""
    done
fi

# Set IAM permissions for service account
echo -e "\n${BOLD}Setting IAM permissions for secrets...${NC}"
read -p "Enter the service account email that needs access to these secrets (e.g., orchestra-prod-sa@$PROJECT_ID.iam.gserviceaccount.com): " service_account

if [ -n "$service_account" ]; then
    echo -e "${YELLOW}Setting IAM permissions for $service_account...${NC}"
    
    # Get all secrets with the production suffix
    secrets=$(gcloud secrets list --filter="name ~ .*-prod$" --format="value(name)")
    
    for secret in $secrets; do
        echo -e "${YELLOW}Granting access to '$secret'...${NC}"
        gcloud secrets add-iam-policy-binding $secret \
            --member="serviceAccount:$service_account" \
            --role="roles/secretmanager.secretAccessor"
    done
    
    echo -e "${GREEN}IAM permissions set successfully${NC}"
else
    echo -e "${YELLOW}Skipping IAM permission setup${NC}"
fi

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Production secrets setup completed!${NC}"
echo -e "${YELLOW}The following secrets have been configured:${NC}"

# List all production secrets
gcloud secrets list --filter="name ~ .*-prod$" --format="table(name)"

echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Ensure your Terraform configuration references these secrets"
echo -e "2. Update your GitHub Actions secrets if using CI/CD"
echo -e "3. Run Terraform with prod.tfvars to deploy to production"
echo -e "${BLUE}======================================================${NC}"
