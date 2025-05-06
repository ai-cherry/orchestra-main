#!/bin/bash
# Wrapper script to integrate GitHub organization secrets mapping with the setup process
# This script detects and uses existing GitHub CLI installation or guides the user to install it

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as part of a larger setup
CALLED_FROM_SETUP=false
if [ "$1" == "--from-setup" ]; then
  CALLED_FROM_SETUP=true
  shift
fi

echo -e "${BLUE}=== GitHub Organization Secrets Setup ===${NC}"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo -e "${YELLOW}GitHub CLI (gh) is not installed. It's required for GitHub organization secrets mapping.${NC}"
  
  if [ "$CALLED_FROM_SETUP" = true ]; then
    # If running from setup, ask if they want to install GitHub CLI
    read -p "Would you like to install GitHub CLI now? (y/n): " INSTALL_GH
    if [[ "$INSTALL_GH" =~ ^[Yy]$ ]]; then
      echo -e "${BLUE}Installing GitHub CLI...${NC}"
      
      # Detect OS
      if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        echo -e "${YELLOW}Running Linux installation for GitHub CLI${NC}"
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh
      elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        echo -e "${YELLOW}Running macOS installation for GitHub CLI${NC}"
        if command -v brew &> /dev/null; then
          brew install gh
        else
          echo -e "${RED}Homebrew is not installed. Please install Homebrew first:${NC}"
          echo "https://brew.sh/"
          exit 1
        fi
      else
        echo -e "${RED}Unsupported operating system for automatic installation.${NC}"
        echo "Please install GitHub CLI manually: https://cli.github.com/manual/installation"
        exit 1
      fi
      
      echo -e "${GREEN}GitHub CLI installed successfully!${NC}"
    else
      echo -e "${YELLOW}Skipping GitHub CLI installation. GitHub organization secrets will not be mapped.${NC}"
      echo -e "${YELLOW}You can run this script later after installing GitHub CLI.${NC}"
      exit 0
    fi
  else
    # If running standalone, just provide instructions
    echo -e "${RED}Please install GitHub CLI first:${NC}"
    echo "https://cli.github.com/manual/installation"
    exit 1
  fi
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
  echo -e "${YELLOW}You need to authenticate with GitHub CLI.${NC}"
  read -p "Would you like to authenticate now? (y/n): " AUTH_GH
  if [[ "$AUTH_GH" =~ ^[Yy]$ ]]; then
    gh auth login
  else
    echo -e "${YELLOW}Skipping GitHub authentication. GitHub organization secrets will not be mapped.${NC}"
    echo -e "${YELLOW}You can run this script later after authenticating with GitHub.${NC}"
    exit 0
  fi
fi

# Get organization name
ORG_NAME=$(gh repo view --json owner -q .owner.login 2>/dev/null || echo "")

if [ -z "$ORG_NAME" ]; then
  # Attempt to extract from remote URL if gh repo view failed
  REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
  if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+) ]]; then
    ORG_NAME="${BASH_REMATCH[1]}"
  fi
fi

if [ -z "$ORG_NAME" ]; then
  echo -e "${YELLOW}Could not determine organization name automatically.${NC}"
  read -p "Please enter your GitHub organization name (or press Enter to skip): " ORG_NAME
  
  if [ -z "$ORG_NAME" ]; then
    echo -e "${YELLOW}No organization name provided. GitHub organization secrets will not be mapped.${NC}"
    exit 0
  fi
fi

echo -e "${GREEN}Using GitHub organization: $ORG_NAME${NC}"

# Determine which script to run based on context
if [ "$CALLED_FROM_SETUP" = true ] || [ "$1" == "--ci" ]; then
  # If called from setup or with CI flag, use non-interactive script
  echo -e "${BLUE}Running non-interactive GitHub organization secrets mapping...${NC}"
  "$SCRIPT_DIR/update_github_org_secrets_ci.sh" --org "$ORG_NAME" --yes
else
  # Otherwise use interactive script
  echo -e "${BLUE}Running interactive GitHub organization secrets mapping...${NC}"
  "$SCRIPT_DIR/update_github_org_secrets.sh"
fi

# Print success message
echo -e "\n${GREEN}GitHub organization secrets mapped successfully!${NC}"
echo -e "${YELLOW}Note: GitHub secrets are encrypted and cannot be retrieved directly.${NC}"
echo -e "${YELLOW}You will need to set the actual values in your .env file.${NC}"
echo -e "${YELLOW}See docs/github_org_secrets_mapping.md for more information.${NC}"

exit 0
