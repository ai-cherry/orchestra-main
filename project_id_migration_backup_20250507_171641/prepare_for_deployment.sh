#!/bin/bash
# prepare_for_deployment.sh - Script to prepare environment for Orchestra deployment
#
# This script will:
# 1. Install necessary tools (Docker, Google Cloud SDK)
# 2. Set up authentication for GCP
# 3. Create required directories and prepare deployment files
# 4. Guide through deployment options

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Orchestra Deployment Preparation                   ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Create directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p /tmp/credentials

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Install Docker if not installed
if ! command_exists docker; then
  echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
  
  # Install Docker using the convenience script
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  
  # Add current user to docker group to avoid using sudo
  sudo usermod -aG docker $USER
  
  echo -e "${GREEN}Docker installed successfully.${NC}"
  echo -e "${YELLOW}You may need to log out and log back in for group changes to take effect.${NC}"
else
  echo -e "${GREEN}Docker is already installed.${NC}"
fi

# Install Google Cloud SDK if not installed
if ! command_exists gcloud; then
  echo -e "${YELLOW}Google Cloud SDK not found. Installing gcloud...${NC}"
  
  # Install Google Cloud SDK
  curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-latest-linux-x86_64.tar.gz
  tar -xf google-cloud-sdk-latest-linux-x86_64.tar.gz
  ./google-cloud-sdk/install.sh --quiet
  
  # Add to PATH for current session
  export PATH="$PATH:$HOME/google-cloud-sdk/bin"
  
  # Add to shell profile for persistence
  echo 'export PATH="$PATH:$HOME/google-cloud-sdk/bin"' >> ~/.bashrc
  
  echo -e "${GREEN}Google Cloud SDK installed successfully.${NC}"
else
  echo -e "${GREEN}Google Cloud SDK is already installed.${NC}"
fi

# Auth setup
echo -e "${YELLOW}Setting up GCP authentication...${NC}"
echo -e "${YELLOW}IMPORTANT: You will be prompted to log in with your GCP account.${NC}"
gcloud auth login

# Set project
echo -e "${YELLOW}Setting GCP project to agi-baby-cherry...${NC}"
gcloud config set project agi-baby-cherry

# Create service account key
echo -e "${YELLOW}Setting up service account key...${NC}"
echo -e "${BLUE}You have two options:${NC}"
echo "1. Create a new service account key"
echo "2. Use an existing key JSON file"
read -p "Choose an option (1/2): " key_option

if [ "$key_option" == "1" ]; then
  echo -e "${YELLOW}Creating new service account key for vertex-agent...${NC}"
  gcloud iam service-accounts keys create /tmp/credentials/vertex-agent-key.json \
    --iam-account=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com
  echo -e "${GREEN}Key created at /tmp/credentials/vertex-agent-key.json${NC}"
else
  echo -e "${YELLOW}Please paste the contents of your service account key JSON below.${NC}"
  echo -e "${YELLOW}Press Ctrl+D when finished.${NC}"
  cat > /tmp/credentials/vertex-agent-key.json
  echo -e "${GREEN}Key saved to /tmp/credentials/vertex-agent-key.json${NC}"
fi

# Copy to the expected location
cp /tmp/credentials/vertex-agent-key.json /tmp/vertex-agent-key.json
chmod 600 /tmp/vertex-agent-key.json

# Set environment variables
echo -e "${YELLOW}Setting up environment variables...${NC}"
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json

# Check Redis configuration
echo -e "${YELLOW}Checking Redis configuration...${NC}"
if grep -q "REDIS_HOST=localhost" .env; then
  echo -e "${RED}Warning: Redis is configured to use localhost in .env${NC}"
  echo -e "${YELLOW}For production deployment, you should update this to point to a managed Redis instance.${NC}"
  
  echo -e "${BLUE}Do you want to update the Redis configuration now? (y/n)${NC}"
  read -p "Update Redis config? " update_redis
  
  if [ "$update_redis" == "y" ]; then
    read -p "Enter Redis host (e.g., redis-12345.c12345.us-central1-1.gcp.cloud.redislabs.com): " redis_host
    read -p "Enter Redis port (default: 6379): " redis_port
    redis_port=${redis_port:-6379}
    
    # Update .env file
    sed -i "s/REDIS_HOST=localhost/REDIS_HOST=$redis_host/" .env
    sed -i "s/REDIS_PORT=6379/REDIS_PORT=$redis_port/" .env
    
    echo -e "${GREEN}Redis configuration updated in .env${NC}"
  fi
fi

# Test authentication
echo -e "${YELLOW}Testing GCP authentication...${NC}"
python test_gcp_auth.py

# Display deployment options
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Deployment Options                                 ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Your environment is now prepared for deployment. You can:${NC}"
echo -e "1. ${YELLOW}Deploy to Cloud Run (recommended for quick deployment):${NC}"
echo -e "   ./deploy_to_cloud_run.sh prod"
echo ""
echo -e "2. ${YELLOW}Deploy infrastructure with Terraform:${NC}"
echo -e "   cd infra && ./run_terraform.sh"
echo ""
echo -e "3. ${YELLOW}Use GitHub Actions CI/CD (recommended for production):${NC}"
echo -e "   Commit and push your changes to trigger GitHub Actions workflows"
echo -e "   (Ensure GitHub repository secrets are configured properly)"
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Deployment preparation complete!${NC}"
