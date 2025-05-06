#!/bin/bash
# Setup credentials for AI Orchestra
# This script sets up the necessary credentials for the AI Orchestra project

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-west4"}
SECRET_MANAGEMENT_KEY_PATH=${SECRET_MANAGEMENT_KEY_PATH:-"$HOME/.config/gcloud/keys/secret-management-key.json"}
PROJECT_ADMIN_KEY_PATH=${PROJECT_ADMIN_KEY_PATH:-"$HOME/.config/gcloud/keys/project-admin-key.json"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if key files exist
if [ ! -f "$SECRET_MANAGEMENT_KEY_PATH" ]; then
    echo -e "${RED}Error: Secret management key file not found at $SECRET_MANAGEMENT_KEY_PATH${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ADMIN_KEY_PATH" ]; then
    echo -e "${RED}Error: Project admin key file not found at $PROJECT_ADMIN_KEY_PATH${NC}"
    exit 1
fi

# Print configuration
echo -e "${BLUE}=== Configuration ===${NC}"
echo -e "Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Secret Management Key: ${GREEN}${SECRET_MANAGEMENT_KEY_PATH}${NC}"
echo -e "Project Admin Key: ${GREEN}${PROJECT_ADMIN_KEY_PATH}${NC}"
echo ""

# Confirm with user
read -p "Do you want to proceed with this configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setup cancelled.${NC}"
    exit 0
fi

# Authenticate with Secret Management service account
echo -e "${BLUE}Authenticating with Secret Management service account...${NC}"
gcloud auth activate-service-account --key-file="$SECRET_MANAGEMENT_KEY_PATH"
echo -e "${GREEN}Authenticated with Secret Management service account${NC}"

# Set the project
echo -e "${BLUE}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Set the region
echo -e "${BLUE}Setting region to ${REGION}...${NC}"
gcloud config set compute/region ${REGION}

# Create API keys in Secret Manager
echo -e "${BLUE}Creating API keys in Secret Manager...${NC}"

# Check if secrets exist
create_secret_if_not_exists() {
    local secret_id=$1
    local description=$2
    
    if ! gcloud secrets describe ${secret_id} &> /dev/null; then
        echo -e "${BLUE}Creating secret: ${secret_id}${NC}"
        gcloud secrets create ${secret_id} --description="${description}"
        echo -e "${GREEN}Created secret: ${secret_id}${NC}"
    else
        echo -e "${YELLOW}Secret already exists: ${secret_id}${NC}"
    fi
}

# Create secrets for LLM providers
create_secret_if_not_exists "openai-api-key" "OpenAI API Key for AI Orchestra"
create_secret_if_not_exists "anthropic-api-key" "Anthropic API Key for AI Orchestra"
create_secret_if_not_exists "gemini-api-key" "Google Gemini API Key for AI Orchestra"

# Authenticate with Project Admin service account
echo -e "${BLUE}Authenticating with Project Admin service account...${NC}"
gcloud auth activate-service-account --key-file="$PROJECT_ADMIN_KEY_PATH"
echo -e "${GREEN}Authenticated with Project Admin service account${NC}"

# Create service account for Cloud Run
echo -e "${BLUE}Creating service account for Cloud Run...${NC}"
SERVICE_ACCOUNT_NAME="orchestra-service-account"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} &> /dev/null; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --display-name="Orchestra Service Account"
    echo -e "${GREEN}Created service account: ${SERVICE_ACCOUNT_EMAIL}${NC}"
else
    echo -e "${YELLOW}Service account already exists: ${SERVICE_ACCOUNT_EMAIL}${NC}"
fi

# Grant necessary roles to the service account
echo -e "${BLUE}Granting necessary roles to the service account...${NC}"
for role in "roles/secretmanager.secretAccessor" "roles/firestore.user" "roles/redis.editor" "roles/storage.objectUser" "roles/aiplatform.user"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="${role}" \
        --condition=None
done

echo -e "${GREEN}Setup completed successfully!${NC}"