#!/bin/bash
# setup_gcp_codespaces.sh - Streamlined GCP Authentication for Codespaces
#
# This script simplifies GCP authentication in Codespaces environments by:
# 1. Using GCP_MASTER_SERVICE_JSON for authentication
# 2. Setting up gcloud CLI
# 3. Configuring default project and region
# 4. Setting up environment variables

set -e  # Exit on error

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}AI Orchestra GCP Codespaces Setup${RESET}"
echo "----------------------------------------"

# Check if running in Codespaces
if [ -z "$CODESPACES" ]; then
    echo -e "${YELLOW}Warning: Not running in GitHub Codespaces. Some features may not work as expected.${RESET}"
fi

# Check if GCP_MASTER_SERVICE_JSON is set
if [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
    echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable is not set.${RESET}"
    echo "Please set this environment variable in your Codespaces secrets."
    echo "Instructions:"
    echo "1. Go to GitHub repository settings"
    echo "2. Navigate to Secrets > Codespaces"
    echo "3. Add a new secret named GCP_MASTER_SERVICE_JSON with your service account JSON"
    exit 1
fi

# Create credentials directory
CREDS_DIR="$HOME/.config/gcloud"
mkdir -p "$CREDS_DIR"

# Create credentials file
CREDS_FILE="$CREDS_DIR/application_default_credentials.json"
echo "$GCP_MASTER_SERVICE_JSON" > "$CREDS_FILE"
echo -e "${GREEN}✓ Created application default credentials file${RESET}"

# Create service account file for gcloud
SA_FILE="/tmp/gcp-credentials.json"
echo "$GCP_MASTER_SERVICE_JSON" > "$SA_FILE"
echo -e "${GREEN}✓ Created temporary service account file${RESET}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}gcloud CLI not found. Installing...${RESET}"
    
    # Download and install Google Cloud SDK
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-latest-linux-x86_64.tar.gz
    tar -xf google-cloud-sdk-latest-linux-x86_64.tar.gz
    ./google-cloud-sdk/install.sh --quiet
    
    # Add to PATH
    echo 'source "$HOME/google-cloud-sdk/path.bash.inc"' >> ~/.bashrc
    echo 'source "$HOME/google-cloud-sdk/completion.bash.inc"' >> ~/.bashrc
    source "$HOME/google-cloud-sdk/path.bash.inc"
    
    echo -e "${GREEN}✓ Installed gcloud CLI${RESET}"
else
    echo -e "${GREEN}✓ gcloud CLI already installed${RESET}"
fi

# Authenticate gcloud
echo "Authenticating with GCP..."
gcloud auth activate-service-account --key-file="$SA_FILE"
echo -e "${GREEN}✓ Authenticated with GCP${RESET}"

# Get project ID from credentials
PROJECT_ID=$(cat "$SA_FILE" | grep -o '"project_id": "[^"]*' | cut -d'"' -f4)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Warning: Could not extract project ID from credentials.${RESET}"
    echo "Please enter your GCP project ID:"
    read PROJECT_ID
else
    echo -e "${GREEN}✓ Extracted project ID: $PROJECT_ID${RESET}"
fi

# Set default project
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✓ Set default project to $PROJECT_ID${RESET}"

# Set default region
DEFAULT_REGION="us-west4"
gcloud config set compute/region "$DEFAULT_REGION"
echo -e "${GREEN}✓ Set default region to $DEFAULT_REGION${RESET}"

# Set environment variables
echo "Setting environment variables..."

# Add to .bashrc if not already there
if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS" ~/.bashrc; then
    echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$CREDS_FILE\"" >> ~/.bashrc
    echo "export GOOGLE_CLOUD_PROJECT=\"$PROJECT_ID\"" >> ~/.bashrc
    echo "export GCP_PROJECT_ID=\"$PROJECT_ID\"" >> ~/.bashrc
    echo "export GCP_REGION=\"$DEFAULT_REGION\"" >> ~/.bashrc
fi

# Set for current session
export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GCP_PROJECT_ID="$PROJECT_ID"
export GCP_REGION="$DEFAULT_REGION"

echo -e "${GREEN}✓ Set environment variables${RESET}"

# Clean up temporary file (optional)
# rm "$SA_FILE"
# echo -e "${GREEN}✓ Cleaned up temporary files${RESET}"

# Verify setup
echo "Verifying setup..."
gcloud auth list
gcloud config list

echo "----------------------------------------"
echo -e "${GREEN}${BOLD}GCP authentication complete!${RESET}"
echo "Project: $PROJECT_ID"
echo "Region: $DEFAULT_REGION"
echo "Credentials: $CREDS_FILE"
echo ""
echo "You can now use GCP services from your Codespaces environment."
echo "To use these credentials in your code, use the GCPAuth helper:"
echo ""
echo "from mcp_server.utils.gcp_auth import GCPAuth"
echo "gcp_auth = GCPAuth.get_instance()"
echo "firestore_client = gcp_auth.get_firestore_client()"
echo ""
echo "Happy coding!"