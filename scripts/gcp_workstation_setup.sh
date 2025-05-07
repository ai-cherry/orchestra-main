#!/bin/bash
# Setup Script for Google Cloud Workstations / Vertex AI Workbench
#
# This script automates the setup of a development environment in Google Cloud Workstations
# or Vertex AI Workbench, installing necessary tools, authenticating with gcloud, configuring
# extensions, and setting environment variables.

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Ask for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# Project and Service Account variables
PROJECT_ID="cherry-ai-project"
SERVICE_ACCOUNT="vertex-agent@cherry-ai-project.iam.gserviceaccount.com"

section "Starting Setup for Google Cloud Workstations / Vertex AI Workbench"
echo "This script will configure your environment with:"
echo "  - Python 3.11, Poetry, Terraform, Docker, and project dependencies"
echo "  - gcloud authentication using $SERVICE_ACCOUNT"
echo "  - Configuration for Gemini Code Assist and Cloud Code extensions"
echo "  - Necessary environment variables including GOOGLE_APPLICATION_CREDENTIALS"
echo ""

# Step 1: Dependency Installation
section "Installing Dependencies"

# Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    sudo apt-get update
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
    success "Python 3.11 installed"
else
    success "Python 3.11 already installed"
fi

# Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3.11 -
    export PATH="$HOME/.local/bin:$PATH"
    success "Poetry installed"
else
    success "Poetry already installed"
fi

# Terraform
if ! command -v terraform &> /dev/null; then
    echo "Installing Terraform..."
    sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt-get update
    sudo apt-get install -y terraform
    success "Terraform installed"
else
    success "Terraform already installed"
fi

# Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    success "Docker installed"
else
    success "Docker already installed"
fi

# Project Dependencies
section "Installing Project Dependencies"
if [ -f "pyproject.toml" ]; then
    echo "Installing dependencies using Poetry..."
    poetry install
    success "Project dependencies installed with Poetry"
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies using pip..."
    python3.11 -m pip install -r requirements.txt
    success "Project dependencies installed with pip"
else
    warning "No pyproject.toml or requirements.txt found. Skipping project dependency installation."
fi

# Step 2: gcloud Authentication
section "Authenticating with gcloud"
if ! command -v gcloud &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    sudo apt-get update
    sudo apt-get install -y google-cloud-sdk
    success "Google Cloud SDK installed"
else
    success "Google Cloud SDK already installed"
fi

echo "Checking gcloud authentication status..."
if ! gcloud auth list --filter=status:ACTIVE | grep -q "$SERVICE_ACCOUNT"; then
    echo "Authenticating with service account $SERVICE_ACCOUNT..."
    # Assuming the key file needs to be retrieved or is available
    if [ -f "service-account-key.json" ]; then
        gcloud auth activate-service-account $SERVICE_ACCOUNT --key-file=service-account-key.json --project=$PROJECT_ID
        success "Authenticated with service account"
    else
        warning "Service account key file not found. Attempting application default credentials..."
        gcloud auth application-default login --project=$PROJECT_ID
        if gcloud auth list --filter=status:ACTIVE | grep -q "$SERVICE_ACCOUNT"; then
            success "Authenticated with application default credentials"
        else
            error "Failed to authenticate with gcloud. Please ensure the service account key is available or manually authenticate."
            exit 1
        fi
    fi
else
    success "Already authenticated with $SERVICE_ACCOUNT"
fi

# Step 3: Configure Extensions
section "Configuring Extensions for Development"

# Gemini Code Assist
echo "Testing Gemini Code Assist integration..."
if gcloud alpha ai code-assist review --source="test_file.py" --project=$PROJECT_ID --category=security --format="value(response)" &> /dev/null; then
    success "Gemini Code Assist integration verified"
else
    warning "Gemini Code Assist test failed. Ensure alpha features are enabled for your account."
fi

# Cloud Code
echo "Checking Cloud Code prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "Installing kubectl for Cloud Code support..."
    sudo apt-get update
    sudo apt-get install -y kubectl
    success "kubectl installed for Cloud Code"
else
    success "kubectl already installed for Cloud Code"
fi

# Step 4: Set Environment Variables
section "Setting Environment Variables"
if [ -f "service-account-key.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account-key.json"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS" >> ~/.bashrc
    success "Set GOOGLE_APPLICATION_CREDENTIALS to $GOOGLE_APPLICATION_CREDENTIALS"
else
    warning "Service account key file not found. GOOGLE_APPLICATION_CREDENTIALS not set. You may need to set this manually."
fi

export GCP_PROJECT_ID=$PROJECT_ID
echo "export GCP_PROJECT_ID=$PROJECT_ID" >> ~/.bashrc
success "Set GCP_PROJECT_ID to $PROJECT_ID"

# Reload bashrc to apply changes
source ~/.bashrc

# Step 5: Document Manual Steps
section "Documentation of Manual Steps"
echo "The following manual steps may be required:"
echo "  1. Service Account Key: If not already present, ensure the service account key file for $SERVICE_ACCOUNT is securely stored or retrieved. You may need to download it from GCP Secret Manager or IAM console."
echo "  2. VS Code Extensions: Configure Gemini Code Assist and Cloud Code extensions in VS Code with your user preferences if specific settings are needed."
echo "  3. Additional Credentials: Set up any user-specific credentials for Docker or Terraform if required for your workflows."
echo ""
warning "Please review these manual steps and complete them if necessary."

# Step 6: Verification
section "Verifying Setup"
echo "Checking installed versions:"
python3.11 --version || error "Python 3.11 not properly installed"
poetry --version || error "Poetry not properly installed"
terraform --version || error "Terraform not properly installed"
docker --version || error "Docker not properly installed"
gcloud --version || error "gcloud SDK not properly installed"
echo ""
if gcloud auth list --filter=status:ACTIVE | grep -q "$SERVICE_ACCOUNT"; then
    success "gcloud authentication verified"
else
    error "gcloud authentication not verified for $SERVICE_ACCOUNT"
fi
echo ""
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    success "GOOGLE_APPLICATION_CREDENTIALS set to $GOOGLE_APPLICATION_CREDENTIALS"
else
    warning "GOOGLE_APPLICATION_CREDENTIALS not set"
fi

# Step 7: Completion
section "Setup Complete"
echo -e "${GREEN}Your Google Cloud Workstation / Vertex AI Workbench environment is now set up!${NC}"
echo ""
echo "Summary of setup:"
echo "  - Python 3.11, Poetry, Terraform, and Docker installed"
echo "  - gcloud authenticated with $SERVICE_ACCOUNT"
echo "  - Gemini Code Assist and Cloud Code extensions configured"
echo "  - Environment variables set (check for GOOGLE_APPLICATION_CREDENTIALS if not set)"
echo ""
echo "Next steps:"
echo "  - Verify manual steps documented above if applicable"
echo "  - Start developing with your configured environment"
echo "  - For troubleshooting, refer to GCP documentation or contact support"