#!/bin/bash
# create_secret.sh
# Script to programmatically create secrets in Google Cloud Secret Manager
# This script includes authentication, API enablement, and proper error handling

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PROJECT_ID="cherry-ai-project"
DEFAULT_REPLICATION_POLICY="automatic"
DEFAULT_ENVIRONMENT="production"

# Parse arguments
SECRET_NAME=$1
SECRET_VALUE=$2
PROJECT_ID=${3:-$DEFAULT_PROJECT_ID}
REPLICATION_POLICY=${4:-$DEFAULT_REPLICATION_POLICY}
ENVIRONMENT=${5:-$DEFAULT_ENVIRONMENT}
LOCATION=${6:-"us-west4"}  # Only used if replication is user-managed

# Display usage information
usage() {
    echo "Usage: ./create_secret.sh SECRET_NAME SECRET_VALUE [PROJECT_ID] [REPLICATION_POLICY] [ENVIRONMENT] [LOCATION]"
    echo ""
    echo "Arguments:"
    echo "  SECRET_NAME        Name of the secret (required)"
    echo "  SECRET_VALUE       Value of the secret (required)"
    echo "  PROJECT_ID         GCP Project ID (default: $DEFAULT_PROJECT_ID)"
    echo "  REPLICATION_POLICY 'automatic' or 'user-managed' (default: $DEFAULT_REPLICATION_POLICY)"
    echo "  ENVIRONMENT        Environment suffix, e.g. 'production', 'dev' (default: $DEFAULT_ENVIRONMENT)"
    echo "  LOCATION           Region for user-managed replication (default: us-west4)"
    echo ""
    echo "Example:"
    echo "  ./create_secret.sh API_KEY \"my-secret-api-key\""
    echo "  ./create_secret.sh DATABASE_PASSWORD \"db-password-123\" cherry-ai-project user-managed staging us-west1"
}

# Validate required arguments
if [ -z "$SECRET_NAME" ] || [ -z "$SECRET_VALUE" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    usage
    exit 1
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env...${NC}"
    source .env

    # Override with .env values if they exist
    PROJECT_ID=${GCP_PROJECT_ID:-$PROJECT_ID}
fi

echo -e "${YELLOW}=== Secret Creation Configuration ===${NC}"
echo -e "Secret Name: $SECRET_NAME"
echo -e "Project ID: $PROJECT_ID"
echo -e "Replication Policy: $REPLICATION_POLICY"
echo -e "Environment: $ENVIRONMENT"
if [ "$REPLICATION_POLICY" == "user-managed" ]; then
    echo -e "Location: $LOCATION"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: Google Cloud SDK (gcloud) is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication to GCP
echo -e "\n${YELLOW}Checking GCP authentication...${NC}"
if ! gcloud auth print-access-token &>/dev/null; then
    echo -e "${RED}Not authenticated to GCP. Running 'gcloud auth login'...${NC}"
    gcloud auth login

    # Check if login was successful
    if ! gcloud auth print-access-token &>/dev/null; then
        echo -e "${RED}Authentication failed. Please run 'gcloud auth login' manually.${NC}"
        exit 1
    fi
fi

# Set project
echo -e "${YELLOW}Setting GCP project ID to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Check if Secret Manager API is enabled
echo -e "${YELLOW}Checking if Secret Manager API is enabled...${NC}"
if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" | grep -q secretmanager.googleapis.com; then
    echo -e "${YELLOW}Secret Manager API is not enabled. Enabling now...${NC}"
    gcloud services enable secretmanager.googleapis.com
    echo -e "${GREEN}Secret Manager API has been enabled.${NC}"
fi

# Full secret ID with environment
FULL_SECRET_ID="${SECRET_NAME}-${ENVIRONMENT}"

# Check if secret already exists
if gcloud secrets describe "$FULL_SECRET_ID" &>/dev/null; then
    echo -e "${YELLOW}Secret $FULL_SECRET_ID already exists. Adding new version...${NC}"
    echo -n "$SECRET_VALUE" | gcloud secrets versions add "$FULL_SECRET_ID" --data-file=- --quiet
    echo -e "${GREEN}✓ Successfully added new version to secret: $FULL_SECRET_ID${NC}"
else
    echo -e "${YELLOW}Creating new secret $FULL_SECRET_ID...${NC}"

    # Create the secret with appropriate replication policy
    if [ "$REPLICATION_POLICY" == "automatic" ]; then
        echo -n "$SECRET_VALUE" | gcloud secrets create "$FULL_SECRET_ID" \
            --replication-policy="automatic" \
            --data-file=- \
            --quiet
    else
        echo -n "$SECRET_VALUE" | gcloud secrets create "$FULL_SECRET_ID" \
            --replication-policy="user-managed" \
            --locations="$LOCATION" \
            --data-file=- \
            --quiet
    fi

    echo -e "${GREEN}✓ Successfully created secret: $FULL_SECRET_ID${NC}"
fi

# Output success message and next steps
echo -e "\n${GREEN}=== Secret Operation Complete! ===${NC}"
echo -e "To view your secret in the GCP Console, visit:"
echo -e "https://console.cloud.google.com/security/secret-manager/secret/$FULL_SECRET_ID?project=$PROJECT_ID"
echo -e "\nTo access this secret programmatically, use:"
echo -e "gcloud secrets versions access latest --secret=\"$FULL_SECRET_ID\""
