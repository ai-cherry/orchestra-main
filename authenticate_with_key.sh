#!/bin/bash
# authenticate_with_key.sh - Script to authenticate with Google Cloud using a service account key

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
KEY_FILE=${2:-"service-account-key.json"}

echo -e "${GREEN}Authenticating with Google Cloud using service account key...${NC}"

# Check if key file exists
if [ ! -f "${KEY_FILE}" ]; then
    echo -e "${RED}Service account key file not found: ${KEY_FILE}${NC}"
    echo -e "${YELLOW}Please provide a valid service account key file.${NC}"
    echo -e "${YELLOW}Usage: ./authenticate_with_key.sh [project_id] [key_file]${NC}"
    exit 1
fi

# Authenticate with service account key
echo -e "${GREEN}Authenticating with service account key...${NC}"
gcloud auth activate-service-account --key-file="${KEY_FILE}"

# Set project
echo -e "${GREEN}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project "${PROJECT_ID}"

# Verify authentication
echo -e "${GREEN}Verifying authentication...${NC}"
gcloud auth list

echo -e "${GREEN}Authentication successful!${NC}"
echo -e "${GREEN}You can now proceed with deployment.${NC}"

# Export environment variable for Google Application Credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/${KEY_FILE}"
echo -e "${GREEN}Exported GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}${NC}"
echo -e "${YELLOW}To use this in your current shell, run:${NC}"
echo -e "${YELLOW}export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/${KEY_FILE}\"${NC}"