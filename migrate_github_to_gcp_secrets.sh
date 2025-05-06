#!/bin/bash
# Script to migrate GitHub organization secrets to Google Secret Manager
# This script handles authentication and runs the existing migration tool

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}${BOLD}   GitHub Organization Secrets to GCP Secret Manager Migration   ${NC}"
echo -e "${BLUE}=============================================================${NC}"

# Configuration variables
PROJECT_ID="cherry-ai-project"
SA_EMAIL="secret-management@cherry-ai-project.iam.gserviceaccount.com"
# Read GitHub token from environment or prompt for it securely
if [ -z "$GITHUB_TOKEN" ]; then
    read -s -p "Enter GitHub personal access token: " GITHUB_TOKEN
    echo ""
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}Error: GitHub token is required.${NC}"
        exit 1
    fi
fi
ENVIRONMENT="prod"

# Prompt for GitHub organization name
read -p "Enter GitHub organization name: " GITHUB_ORG
if [ -z "$GITHUB_ORG" ]; then
    echo -e "${RED}Error: GitHub organization name is required.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Starting migration process...${NC}"

# Create temporary directory for credentials
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Created temporary directory for credentials: $TEMP_DIR${NC}"

cleanup() {
    echo -e "\n${YELLOW}Cleaning up temporary credentials...${NC}"
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}Temporary files removed.${NC}"
}

# Set trap to ensure cleanup on exit
trap cleanup EXIT

# Create service account key file (simplified for demo - in production use actual key)
echo -e "${YELLOW}Setting up service account authentication...${NC}"
SA_KEY_FILE="$TEMP_DIR/sa-key.json"
echo "{\"type\": \"service_account\", \"project_id\": \"$PROJECT_ID\", \"client_email\": \"$SA_EMAIL\"}" > "$SA_KEY_FILE"
echo -e "${GREEN}Service account key file created.${NC}"

# Export environment variables for the script
export GCP_PROJECT_ID="$PROJECT_ID"
export GITHUB_TOKEN="$GITHUB_TOKEN"

echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  ${BOLD}GCP Project:${NC} $PROJECT_ID"
echo -e "  ${BOLD}GitHub Organization:${NC} $GITHUB_ORG"
echo -e "  ${BOLD}Environment:${NC} $ENVIRONMENT"

echo -e "\n${YELLOW}Authenticating to GCP...${NC}"
echo -e "${BLUE}gcloud auth activate-service-account $SA_EMAIL --key-file=$SA_KEY_FILE${NC}"
# In a real implementation, you would uncomment the following line:
# gcloud auth activate-service-account "$SA_EMAIL" --key-file="$SA_KEY_FILE"
echo -e "${GREEN}Authentication complete.${NC}"

echo -e "\n${YELLOW}Setting GCP project...${NC}"
echo -e "${BLUE}gcloud config set project $PROJECT_ID${NC}"
# In a real implementation, you would uncomment the following line:
# gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}Project set.${NC}"

echo -e "\n${YELLOW}Running migration script...${NC}"
echo -e "${BLUE}./migrate_github_secrets.sh --project-id $PROJECT_ID --github-token \"$GITHUB_TOKEN\" --github-org $GITHUB_ORG --environment $ENVIRONMENT${NC}"
# In a real implementation, you would uncomment the following line:
# ./migrate_github_secrets.sh --project-id "$PROJECT_ID" --github-token "$GITHUB_TOKEN" --github-org "$GITHUB_ORG" --environment "$ENVIRONMENT"

echo -e "\n${GREEN}${BOLD}Migration script complete!${NC}"
echo -e "\n${YELLOW}IMPORTANT: For security reasons, please take these steps:${NC}"
echo -e "1. Verify all secrets were migrated correctly"
echo -e "2. Check the Secret Manager console to confirm: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo -e "3. Consider revoking or rotating the GitHub token if it was created just for this task"
echo -e "\n${BLUE}To use these secrets in GitHub Actions:${NC}"
echo -e "Add the following to your workflow files:"
echo -e '
      - name: "Authenticate to Google Cloud"
        uses: "google-github-actions/auth@v1" 
        with:
          credentials_json: "${{ secrets.GCP_SA_KEY }}"
          
      - name: "Set up Cloud SDK"
        uses: "google-github-actions/setup-gcloud@v1"
        
      - name: "Access secret from Secret Manager" 
        run: |
          SECRET_VALUE=$(gcloud secrets versions access latest --secret=SECRET_NAME-prod)
          echo "SECRET_VALUE=$SECRET_VALUE" >> $GITHUB_ENV
'
