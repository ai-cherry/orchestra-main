#!/bin/bash
# credential_manager.sh - Central credential management for AI Orchestra

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   AI Orchestra Credential Manager"
echo "=================================================="
echo -e "${NC}"

# Create secure credential storage
echo -e "${YELLOW}Creating secure credential storage...${NC}"
mkdir -p ~/.orchestra/credentials
chmod 700 ~/.orchestra/credentials

# Check for required environment variables
if [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
  echo -e "${YELLOW}GCP_MASTER_SERVICE_JSON not set. Skipping GCP credential setup.${NC}"
else
  # Store GCP credentials securely
  echo -e "${YELLOW}Storing GCP master service account...${NC}"
  echo "$GCP_MASTER_SERVICE_JSON" > ~/.orchestra/credentials/gcp-master.json
  chmod 600 ~/.orchestra/credentials/gcp-master.json
  echo -e "${GREEN}✅ GCP master service account stored${NC}"
fi

if [ -z "$GH_CLASSIC_PAT_TOKEN" ]; then
  echo -e "${YELLOW}GH_CLASSIC_PAT_TOKEN not set. Skipping GitHub token setup.${NC}"
else
  # Store GitHub token securely
  echo -e "${YELLOW}Storing GitHub token...${NC}"
  echo "$GH_CLASSIC_PAT_TOKEN" > ~/.orchestra/credentials/github-token.txt
  chmod 600 ~/.orchestra/credentials/github-token.txt
  echo -e "${GREEN}✅ GitHub token stored${NC}"
fi

if [ -z "$GH_FINE_GRAINED_PAT_TOKEN" ]; then
  echo -e "${YELLOW}GH_FINE_GRAINED_PAT_TOKEN not set. Skipping GitHub fine-grained token setup.${NC}"
else
  # Store GitHub fine-grained token securely
  echo -e "${YELLOW}Storing GitHub fine-grained token...${NC}"
  echo "$GH_FINE_GRAINED_PAT_TOKEN" > ~/.orchestra/credentials/github-fine-grained-token.txt
  chmod 600 ~/.orchestra/credentials/github-fine-grained-token.txt
  echo -e "${GREEN}✅ GitHub fine-grained token stored${NC}"
fi

# Create credential helper functions
echo -e "${YELLOW}Creating credential helper functions...${NC}"
cat > ~/.orchestra/credential_helpers.sh << 'EOL'
#!/bin/bash
# Helper functions for credential access

# GCP Master Service Account
function use_gcp_master() {
  if [ -f ~/.orchestra/credentials/gcp-master.json ]; then
    export GOOGLE_APPLICATION_CREDENTIALS=~/.orchestra/credentials/gcp-master.json
    gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
    gcloud config set project cherry-ai-project
    gcloud config set compute/region us-west4
    echo "✅ Using GCP Master Service Account"
  else
    echo "❌ GCP Master Service Account not found"
    return 1
  fi
}

# GitHub Classic Token
function use_github_token() {
  if [ -f ~/.orchestra/credentials/github-token.txt ]; then
    export GITHUB_TOKEN=$(cat ~/.orchestra/credentials/github-token.txt)
    echo "✅ GitHub token configured"
  else
    echo "❌ GitHub token not found"
    return 1
  fi
}

# GitHub Fine-Grained Token
function use_github_fine_grained_token() {
  if [ -f ~/.orchestra/credentials/github-fine-grained-token.txt ]; then
    export GITHUB_FINE_GRAINED_TOKEN=$(cat ~/.orchestra/credentials/github-fine-grained-token.txt)
    echo "✅ GitHub fine-grained token configured"
  else
    echo "❌ GitHub fine-grained token not found"
    return 1
  fi
}

# Configure GitHub CLI
function configure_github_cli() {
  if [ -f ~/.orchestra/credentials/github-token.txt ]; then
    cat ~/.orchestra/credentials/github-token.txt | gh auth login --with-token
    echo "✅ GitHub CLI configured"
  else
    echo "❌ GitHub token not found"
    return 1
  fi
}

# Setup Git Credentials
function setup_git_credentials() {
  if [ -f ~/.orchestra/credentials/github-token.txt ]; then
    git config --global credential.helper store
    GITHUB_TOKEN=$(cat ~/.orchestra/credentials/github-token.txt)
    echo "https://oauth2:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    echo "✅ Git credentials configured"
  else
    echo "❌ GitHub token not found"
    return 1
  fi
}
EOL

chmod +x ~/.orchestra/credential_helpers.sh

# Source helpers in profile if not already there
if ! grep -q "source ~/.orchestra/credential_helpers.sh" ~/.bashrc; then
  echo -e "${YELLOW}Adding credential helpers to .bashrc...${NC}"
  echo "" >> ~/.bashrc
  echo "# AI Orchestra credential helpers" >> ~/.bashrc
  echo "source ~/.orchestra/credential_helpers.sh" >> ~/.bashrc
  echo -e "${GREEN}✅ Credential helpers added to .bashrc${NC}"
else
  echo -e "${YELLOW}Credential helpers already in .bashrc${NC}"
fi

echo -e "${GREEN}"
echo "=================================================="
echo "   Credential Manager Setup Complete!"
echo "=================================================="
echo -e "${NC}"
echo -e "To use credentials, run:"
echo -e "  ${YELLOW}source ~/.orchestra/credential_helpers.sh${NC}"
echo -e "  ${YELLOW}use_gcp_master${NC}"
echo -e "  ${YELLOW}use_github_token${NC}"
echo -e "  ${YELLOW}configure_github_cli${NC}"
echo -e "  ${YELLOW}setup_git_credentials${NC}"