#!/bin/bash
# install_gcloud.sh
# Script to install Google Cloud SDK in the Codespaces environment

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if gcloud is already installed
if command -v gcloud &> /dev/null; then
  log "INFO" "Google Cloud SDK is already installed."
  gcloud --version
  exit 0
fi

# Install dependencies
log "INFO" "Installing dependencies..."
apt-get update && apt-get install -y apt-transport-https ca-certificates gnupg curl

# Add the Google Cloud SDK distribution URI as a package source
log "INFO" "Adding Google Cloud SDK distribution URI as a package source..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
log "INFO" "Importing Google Cloud public key..."
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the Google Cloud SDK
log "INFO" "Installing Google Cloud SDK..."
apt-get update && apt-get install -y google-cloud-sdk

# Verify installation
log "INFO" "Verifying installation..."
gcloud --version

# Set up configuration
log "INFO" "Setting up configuration..."
PROJECT_ID="cherry-ai-project"
ACCOUNT="scoobyjava@cherry-ai.me"

# Set environment variables
log "INFO" "Setting environment variables..."
echo "export CLOUDSDK_CORE_PROJECT=\"${PROJECT_ID}\"" >> ~/.bashrc
echo "export CLOUDSDK_CORE_ACCOUNT=\"${ACCOUNT}\"" >> ~/.bashrc

# Apply changes to current session
export CLOUDSDK_CORE_PROJECT="${PROJECT_ID}"
export CLOUDSDK_CORE_ACCOUNT="${ACCOUNT}"

# Set gcloud configuration
log "INFO" "Setting gcloud configuration..."
gcloud config set project ${PROJECT_ID}
gcloud config set account ${ACCOUNT}

log "SUCCESS" "Google Cloud SDK installed and configured successfully!"
log "INFO" "Project ID: ${PROJECT_ID}"
log "INFO" "Account: ${ACCOUNT}"
log "INFO" "You can now use gcloud commands with this configuration."
log "INFO" "To apply the changes to a new terminal session, run: source ~/.bashrc"