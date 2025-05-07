#!/bin/bash
# connect_repo_and_enable_customization.sh
# Script to connect repository and enable code customization for Gemini Code Assist Enterprise

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Connecting repository and enabling code customization...${NC}"

# Set project ID
PROJECT_ID="cherry-ai-project"
echo -e "${YELLOW}Using project ID: ${PROJECT_ID}${NC}"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
  echo -e "${RED}Error: No active gcloud authentication found.${NC}"
  echo -e "${YELLOW}Please run 'gcloud auth login' or activate a service account first.${NC}"
  exit 1
fi

# Connect repository to Developer Connect
echo -e "${YELLOW}Connecting repository to Developer Connect...${NC}"
gcloud alpha developer-connect repos register github_${PROJECT_ID} \
  --gitlab-host-uri="https://github.com" \
  --project=${PROJECT_ID} \
  --region=us-west4
echo -e "${GREEN}Repository connected successfully${NC}"

# Enable code customization
echo -e "${YELLOW}Enabling code customization...${NC}"
gcloud alpha genai code customize enable \
  --project=${PROJECT_ID} \
  --repos=github_${PROJECT_ID}
echo -e "${GREEN}Code customization enabled successfully${NC}"

# Verify setup
echo -e "${YELLOW}Verifying setup...${NC}"
gcloud alpha genai code customize list --project=${PROJECT_ID}

echo -e "${BLUE}Repository connection and code customization setup complete!${NC}"
echo -e "${GREEN}You can now use Gemini Code Assist Enterprise with the repository context.${NC}"
