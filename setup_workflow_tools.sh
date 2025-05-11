#!/bin/bash
# setup_workflow_tools.sh - Setup script for AI Orchestra workflow tools
# This script installs and configures all the workflow optimization tools

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

section "AI Orchestra Workflow Tools Setup"

echo -e "${BOLD}This script will set up the following workflow optimization tools:${NC}"
echo "  1. Unified Workflow Tool (orchestra.sh)"
echo "  2. Enhanced GitHub Authentication (github_auth.sh)"
echo "  3. Enhanced Deployment Script (deploy_enhanced.sh)"
echo "  4. Optimized GitHub Actions Workflow (optimized-github-workflow.yml)"
echo ""
echo -e "${YELLOW}Do you want to proceed? (y/n)${NC}"
read -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setup cancelled.${NC}"
    exit 0
fi

section "Checking Prerequisites"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. It's recommended for full functionality.${NC}"
    echo -e "${YELLOW}Would you like to install GitHub CLI? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Installing GitHub CLI...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install gh
        else
            echo -e "${RED}Unsupported OS. Please install GitHub CLI manually: https://cli.github.com/manual/installation${NC}"
        fi
    fi
fi

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Google Cloud SDK (gcloud) not found. It's required for deployment functionality.${NC}"
    echo -e "${YELLOW}Would you like to install Google Cloud SDK? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Installing Google Cloud SDK...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-latest-linux-x86_64.tar.gz
            tar -xf google-cloud-sdk-latest-linux-x86_64.tar.gz
            ./google-cloud-sdk/install.sh
            rm google-cloud-sdk-latest-linux-x86_64.tar.gz
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install --cask google-cloud-sdk
        else
            echo -e "${RED}Unsupported OS. Please install Google Cloud SDK manually: https://cloud.google.com/sdk/docs/install${NC}"
        fi
    fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. It's recommended for full functionality.${NC}"
    echo -e "${YELLOW}Would you like to install Docker? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Installing Docker...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            rm get-docker.sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install --cask docker
        else
            echo -e "${RED}Unsupported OS. Please install Docker manually: https://docs.docker.com/get-docker/${NC}"
        fi
    fi
fi

section "Setting Up Workflow Tools"

# Create configuration directory
echo -e "${GREEN}Creating configuration directory...${NC}"
mkdir -p ~/.orchestra/credentials
chmod 700 ~/.orchestra/credentials

# Make scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x orchestra.sh github_auth.sh deploy_enhanced.sh

# Set up GitHub Actions workflow
echo -e "${GREEN}Setting up GitHub Actions workflow...${NC}"
mkdir -p .github/workflows
if [ -f ".github/workflows/ai-orchestra-cicd.yml" ]; then
    echo -e "${YELLOW}GitHub Actions workflow already exists. Would you like to replace it? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp optimized-github-workflow.yml .github/workflows/ai-orchestra-cicd.yml
        echo -e "${GREEN}GitHub Actions workflow updated.${NC}"
    fi
else
    cp optimized-github-workflow.yml .github/workflows/ai-orchestra-cicd.yml
    echo -e "${GREEN}GitHub Actions workflow created.${NC}"
fi

section "Configuring GitHub Authentication"

# Set up GitHub authentication
echo -e "${YELLOW}Would you like to set up GitHub authentication now? (y/n)${NC}"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Setting up GitHub authentication...${NC}"
    ./github_auth.sh
fi

section "Configuring Environment"

# Create environment configuration directory
echo -e "${GREEN}Creating environment configuration directory...${NC}"
mkdir -p config/environments

# Create environment configuration files
echo -e "${GREEN}Creating environment configuration files...${NC}"
if [ ! -f "config/environments/dev.env" ]; then
    cat > config/environments/dev.env << EOF
# Development environment configuration
MEMORY="512Mi"
CPU="1"
MIN_INSTANCES="0"
MAX_INSTANCES="5"
EOF
    echo -e "${GREEN}Created development environment configuration.${NC}"
fi

if [ ! -f "config/environments/prod.env" ]; then
    cat > config/environments/prod.env << EOF
# Production environment configuration
MEMORY="1Gi"
CPU="2"
MIN_INSTANCES="1"
MAX_INSTANCES="20"
EOF
    echo -e "${GREEN}Created production environment configuration.${NC}"
fi

section "Adding Shell Integration"

# Add shell integration
echo -e "${YELLOW}Would you like to add shell integration for the workflow tool? (y/n)${NC}"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SHELL_RC=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        echo -e "${GREEN}Adding shell integration to $SHELL_RC...${NC}"
        
        # Check if integration already exists
        if grep -q "# AI Orchestra Workflow Tool Integration" "$SHELL_RC"; then
            echo -e "${YELLOW}Shell integration already exists. Skipping.${NC}"
        else
            cat >> "$SHELL_RC" << EOF

# AI Orchestra Workflow Tool Integration
alias orchestra="$PWD/orchestra.sh"
EOF
            echo -e "${GREEN}Shell integration added. You can now use 'orchestra' command from anywhere.${NC}"
            echo -e "${YELLOW}Please restart your shell or run 'source $SHELL_RC' to apply the changes.${NC}"
        fi
    else
        echo -e "${YELLOW}Could not find .bashrc or .zshrc. Please add shell integration manually.${NC}"
    fi
fi

section "Setup Complete"

echo -e "${GREEN}Workflow tools setup completed successfully!${NC}"
echo ""
echo -e "${BOLD}Available tools:${NC}"
echo "  - Unified Workflow Tool: ./orchestra.sh"
echo "  - Enhanced GitHub Authentication: ./github_auth.sh"
echo "  - Enhanced Deployment Script: ./deploy_enhanced.sh"
echo "  - Optimized GitHub Actions Workflow: .github/workflows/ai-orchestra-cicd.yml"
echo ""
echo -e "${BOLD}Documentation:${NC}"
echo "  - Workflow Optimization README: WORKFLOW_OPTIMIZATION_README.md"
echo "  - Implementation Summary: IMPLEMENTATION_SUMMARY.md"
echo ""
echo -e "${BLUE}To get started, run:${NC}"
echo "  ./orchestra.sh"
echo ""
echo -e "${GREEN}Happy coding!${NC}"