 #!/bin/bash
# github_auth.sh - GitHub authentication for AI Orchestra

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define cleanup function
cleanup() {
  if [ -f "$TEMP_TOKEN_FILE" ]; then
    rm -f "$TEMP_TOKEN_FILE"
    echo -e "${GREEN}🧹 Cleaned up temporary files${NC}"
  fi
}

# Register cleanup on exit
trap cleanup EXIT

# Handle errors
handle_error() {
  echo -e "${RED}Error occurred at line $1${NC}"
  exit 1
}

trap 'handle_error $LINENO' ERR

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   AI Orchestra GitHub Authentication"
echo "=================================================="
echo -e "${NC}"

# Check for GitHub CLI
if ! command -v gh &> /dev/null; then
  echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
  
  # Check the OS and install accordingly
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux installation
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS installation
    brew install gh
  else
    echo -e "${RED}Unsupported OS. Please install GitHub CLI manually: https://github.com/cli/cli#installation${NC}"
    exit 1
  fi
fi

# Check for required environment variables or stored credentials
if [ -z "$GH_CLASSIC_PAT_TOKEN" ]; then
  # Check if we have stored credentials
  if [ -f ~/.orchestra/credentials/github-token.txt ]; then
    echo -e "${YELLOW}Using stored GitHub token...${NC}"
    GH_CLASSIC_PAT_TOKEN=$(cat ~/.orchestra/credentials/github-token.txt)
  else
    echo -e "${RED}Error: GH_CLASSIC_PAT_TOKEN environment variable not set and no stored credentials found${NC}"
    echo -e "${YELLOW}Run credential_manager.sh first to set up credentials${NC}"
    exit 1
  fi
fi

# Configure GitHub CLI with token
echo -e "${YELLOW}Configuring GitHub CLI...${NC}"
echo "$GH_CLASSIC_PAT_TOKEN" | gh auth login --with-token
if ! gh auth status; then
  echo -e "${RED}GitHub CLI authentication failed${NC}"
  exit 1
fi
echo -e "${GREEN}✅ GitHub CLI configured${NC}"

# Set up git configuration
echo -e "${YELLOW}Setting up git configuration...${NC}"
git config --global credential.helper store

# Create git credentials file
TEMP_TOKEN_FILE=$(mktemp)
chmod 600 "$TEMP_TOKEN_FILE"
echo "https://oauth2:$GH_CLASSIC_PAT_TOKEN@github.com" > "$TEMP_TOKEN_FILE"
mkdir -p ~/.git
cp "$TEMP_TOKEN_FILE" ~/.git-credentials
chmod 600 ~/.git-credentials

echo -e "${GREEN}✅ Git credentials configured${NC}"

# Check if fine-grained token is available
if [ -n "$GH_FINE_GRAINED_PAT_TOKEN" ] || [ -f ~/.orchestra/credentials/github-fine-grained-token.txt ]; then
  if [ -z "$GH_FINE_GRAINED_PAT_TOKEN" ]; then
    GH_FINE_GRAINED_PAT_TOKEN=$(cat ~/.orchestra/credentials/github-fine-grained-token.txt)
  fi
  
  echo -e "${YELLOW}Fine-grained token available. Setting up environment variable...${NC}"
  export GITHUB_FINE_GRAINED_TOKEN="$GH_FINE_GRAINED_PAT_TOKEN"
  echo -e "${GREEN}✅ Fine-grained token configured${NC}"
fi

# Verify GitHub access
echo -e "${YELLOW}Verifying GitHub access...${NC}"
if gh repo list --limit 1 > /dev/null 2>&1; then
  echo -e "${GREEN}✅ GitHub access verified${NC}"
else
  echo -e "${RED}❌ Could not access GitHub repositories. Check token permissions.${NC}"
  exit 1
fi

echo -e "${GREEN}"
echo "=================================================="
echo "   GitHub Authentication Complete!"
echo "=================================================="
echo -e "${NC}"
echo -e "You can now use GitHub CLI and Git with your authenticated account."
echo -e ""
echo -e "GitHub CLI status:"
gh auth status