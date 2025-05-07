#!/bin/bash
# setup_gemini_enterprise.sh
# Setup script for Gemini Code Assist Enterprise with Google Cloud Code in GitHub Codespaces

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Gemini Code Assist Enterprise in Codespaces...${NC}"

# 1. Authentication Configuration
echo -e "${YELLOW}Configuring authentication...${NC}"

# Add GOOGLE_APPLICATION_CREDENTIALS to .env file if it doesn't exist
if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS" .env 2>/dev/null; then
  echo 'GOOGLE_APPLICATION_CREDENTIALS="service-account.json"' >> .env
  echo -e "${GREEN}Added GOOGLE_APPLICATION_CREDENTIALS to .env${NC}"
else
  echo -e "${GREEN}GOOGLE_APPLICATION_CREDENTIALS already exists in .env${NC}"
fi

# Check if FULL_SERVICE_ACCOUNT_JSON is set
if [ -z "$FULL_SERVICE_ACCOUNT_JSON" ]; then
  echo -e "${RED}Error: FULL_SERVICE_ACCOUNT_JSON environment variable is not set.${NC}"
  echo -e "${YELLOW}Please set this variable with your service account JSON content.${NC}"
  echo -e "Example: export FULL_SERVICE_ACCOUNT_JSON=\$(cat /path/to/your-service-account.json)"
  exit 1
fi

# Write service account JSON to file
echo "$FULL_SERVICE_ACCOUNT_JSON" > service-account.json
echo -e "${GREEN}Created service-account.json${NC}"

# Activate service account
echo -e "${YELLOW}Activating service account...${NC}"
gcloud auth activate-service-account --key-file=service-account.json
echo -e "${GREEN}Service account activated${NC}"

# Extract project ID from service account file
PROJECT_ID=$(jq -r '.project_id' service-account.json)
if [ -z "$PROJECT_ID" ]; then
  echo -e "${YELLOW}Could not extract project_id from service account, using cherry-ai-project as default${NC}"
  PROJECT_ID="cherry-ai-project"
fi

# Set default project
gcloud config set project $PROJECT_ID
echo -e "${GREEN}Set default project to $PROJECT_ID${NC}"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudaicompanion.googleapis.com
echo -e "${GREEN}Cloud AI Companion API enabled${NC}"

# 2. Code Customization Setup
echo -e "${YELLOW}Setting up Developer Connect for code customization...${NC}"

# Register GitHub repository with Developer Connect
echo -e "${YELLOW}Registering repository with Developer Connect...${NC}"
gcloud alpha developer-connect repos register github_${PROJECT_ID} \
  --gitlab-host-uri="https://github.com" \
  --project=$PROJECT_ID \
  --region=us-west4

# Enable code customization
echo -e "${YELLOW}Enabling code customization...${NC}"
gcloud alpha genai code customize enable \
  --project=$PROJECT_ID \
  --repos=github_${PROJECT_ID}

# Verify Region Compatibility
echo -e "${YELLOW}Verifying region compatibility...${NC}"
gcloud alpha genai code customize list --project=$PROJECT_ID

echo -e "${BLUE}Setup complete! Gemini Code Assist Enterprise is now configured.${NC}"
echo -e "${YELLOW}Important: Before ending your session, run the following cleanup command:${NC}"
echo -e "${RED}rm service-account.json && unset GOOGLE_APPLICATION_CREDENTIALS${NC}"
echo ""
echo -e "${GREEN}You can now use Gemini Code Assist Enterprise with the following shortcuts:${NC}"
echo -e "- Press ${BLUE}Ctrl+I${NC} (Win/Linux) or ${BLUE}Cmd+I${NC} (Mac) and try prompts like:"
echo -e "  ${YELLOW}/generate${NC} Vertex AI pipeline with BigQuery input"
echo -e "  ${YELLOW}/doc${NC} this Cloud Function with security warnings"
echo -e "  ${YELLOW}/fix${NC} Redis connection timeout in line 42"
