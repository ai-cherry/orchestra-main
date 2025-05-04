#!/bin/bash
# cleanup_gemini_credentials.sh
# Script to safely remove credentials after using Gemini Code Assist Enterprise

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Cleaning up Gemini Code Assist Enterprise credentials...${NC}"

# Remove service account JSON file if it exists
if [ -f "service-account.json" ]; then
  echo -e "${YELLOW}Removing service account credentials file...${NC}"
  rm service-account.json
  echo -e "${GREEN}Removed service-account.json${NC}"
else
  echo -e "${YELLOW}service-account.json not found, no action needed.${NC}"
fi

# Unset environment variable
echo -e "${YELLOW}Unsetting GOOGLE_APPLICATION_CREDENTIALS environment variable...${NC}"
unset GOOGLE_APPLICATION_CREDENTIALS
echo -e "${GREEN}Unset GOOGLE_APPLICATION_CREDENTIALS${NC}"

# Revoke access token to prevent lingering authorization
echo -e "${YELLOW}Revoking active gcloud token...${NC}"
gcloud auth revoke --all > /dev/null 2>&1 || echo -e "${YELLOW}No active gcloud credentials to revoke${NC}"

echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}Your Gemini Code Assist Enterprise credentials have been safely removed.${NC}"
echo -e "${YELLOW}For security, make sure to properly manage any environment variables in your Codespace settings.${NC}"
