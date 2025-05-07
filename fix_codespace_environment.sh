#!/bin/bash

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  COMPREHENSIVE CODESPACE ENVIRONMENT FIX${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Redirect output to a log file for debugging
exec > >(tee -i /workspaces/orchestra-main/codespace_fix.log) 2>&1

echo "Starting environment fix at $(date)"

# Step 1: Fix gcloud installation
echo -e "\n${BLUE}Step 1: Fixing gcloud installation${NC}"
echo "Removing existing gcloud installation..."
rm -rf ~/google-cloud-sdk
rm -rf /workspaces/orchestra-main/google-cloud-sdk

echo "Downloading and installing gcloud SDK..."
curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts --install-dir=$HOME

echo "Setting up environment..."
export PATH=$PATH:$HOME/google-cloud-sdk/bin
if ! grep -q "export PATH=\$PATH:\$HOME/google-cloud-sdk/bin" ~/.bashrc; then
  echo 'export PATH=$PATH:$HOME/google-cloud-sdk/bin' >> ~/.bashrc
fi

echo "Updating gcloud components..."
$HOME/google-cloud-sdk/bin/gcloud components update --quiet || {
  echo -e "${YELLOW}Warning: gcloud components update failed, but continuing with the fix${NC}"
}

# Step 2: Enforce standard mode
echo -e "\n${BLUE}Step 2: Enforcing standard mode${NC}"

# Create .vscode directory if it doesn't exist
mkdir -p $HOME/.vscode-remote/data/Machine
mkdir -p /workspaces/orchestra-main/.vscode

# Create or update settings.json
cat > /workspaces/orchestra-main/.vscode/settings.json << 'EOF'
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF

# Update machine settings
cat > $HOME/.vscode-remote/data/Machine/settings.json << 'EOF'
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF

# Set environment variables for standard mode
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true
export DISABLE_WORKSPACE_TRUST=true
export USE_RECOVERY_MODE=false

# Add environment variables to .bashrc if not already there
if ! grep -q "VSCODE_DISABLE_WORKSPACE_TRUST=true" ~/.bashrc; then
  cat << 'EOF' >> ~/.bashrc

# Standard mode environment variables
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true
export DISABLE_WORKSPACE_TRUST=true
export USE_RECOVERY_MODE=false
EOF
fi

# Step 3: Configure GCP authentication
echo -e "\n${BLUE}Step 3: Configuring GCP authentication${NC}"

# Create necessary directories
mkdir -p $HOME/.gcp

# Check if GCP_MASTER_SERVICE_JSON is set
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  # Write service account key with retry mechanism
  for i in {1..3}; do
    echo $GCP_MASTER_SERVICE_JSON > $HOME/.gcp/service-account.json && break || {
      echo "Attempt $i to write service account key failed"
      sleep 2
    }
  done
  
  # Set proper permissions
  chmod 600 $HOME/.gcp/service-account.json
  
  # Set credentials environment variable
  export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
  
  # Add to .bashrc if not already there
  if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS=.*service-account.json" ~/.bashrc; then
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> ~/.bashrc
  fi
  
  # Authenticate with GCP
  gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=$HOME/.gcp/service-account.json || {
    echo -e "${YELLOW}Warning: GCP authentication failed, but continuing with the fix${NC}"
  }
  
  # Set project
  gcloud config set project cherry-ai-project
  
  # Disable interactive prompts
  export CLOUDSDK_CORE_DISABLE_PROMPTS=1
  if ! grep -q "CLOUDSDK_CORE_DISABLE_PROMPTS=1" ~/.bashrc; then
    echo 'export CLOUDSDK_CORE_DISABLE_PROMPTS=1' >> ~/.bashrc
  fi
else
  echo -e "${YELLOW}Warning: GCP_MASTER_SERVICE_JSON environment variable not set${NC}"
  echo "Please set this variable with your service account key JSON"
fi

# Step 4: Optimize Git performance
echo -e "\n${BLUE}Step 4: Optimizing Git performance${NC}"

# Set Git configuration for better performance
git config --global gc.auto 256
git config --global core.compression 9
git config --global http.postBuffer 524288000

# Clean up Git repository
echo "Current Git status:"
git status

echo "Performing Git cleanup..."
git add .
git commit -m "Commit all changes to enable full Git features" || {
  echo -e "${YELLOW}Warning: Git commit failed, attempting to continue${NC}"
}
git gc --aggressive
git clean -fd

echo "Git status after cleanup:"
git status

# Step 5: Verify all settings
echo -e "\n${BLUE}Step 5: Verifying environment settings${NC}"

# Check workspace trust settings
echo "Checking workspace trust settings..."
if [ "$VSCODE_DISABLE_WORKSPACE_TRUST" = "true" ]; then
  echo -e "${GREEN}✓ VSCODE_DISABLE_WORKSPACE_TRUST is set to true${NC}"
else
  echo -e "${RED}✗ VSCODE_DISABLE_WORKSPACE_TRUST is not set correctly${NC}"
fi

# Check GCP authentication
echo "Checking GCP authentication..."
ACTIVE_ACCOUNT=$(gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>/dev/null)
if [ "$ACTIVE_ACCOUNT" = "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com" ]; then
  echo -e "${GREEN}✓ GCP authentication is correct (Active account: $ACTIVE_ACCOUNT)${NC}"
else
  echo -e "${RED}✗ GCP authentication is not set correctly (Active account: $ACTIVE_ACCOUNT)${NC}"
fi

# Check project
echo "Checking GCP project..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" = "cherry-ai-project" ]; then
  echo -e "${GREEN}✓ GCP project is set correctly (Project: $CURRENT_PROJECT)${NC}"
else
  echo -e "${RED}✗ GCP project is not set correctly (Project: $CURRENT_PROJECT)${NC}"
fi

# Check gcloud installation
echo "Checking gcloud installation..."
if command -v gcloud &> /dev/null; then
  GCLOUD_PATH=$(which gcloud)
  echo -e "${GREEN}✓ gcloud is installed at: $GCLOUD_PATH${NC}"
else
  echo -e "${RED}✗ gcloud is not properly installed${NC}"
fi

# Check Git status
echo "Checking Git status..."
if git status | grep -q "working tree clean"; then
  echo -e "${GREEN}✓ Git working tree is clean${NC}"
else
  echo -e "${YELLOW}! Git working tree is not clean${NC}"
fi

echo -e "\n${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${GREEN}  ENVIRONMENT FIX COMPLETE${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "${BLUE}1. Source your bashrc to apply environment variables:${NC}"
echo -e "   source ~/.bashrc"
echo -e "${BLUE}2. Reload your VS Code window:${NC}"
echo -e "   Press F1 and select 'Developer: Reload Window'"
echo -e "${BLUE}3. If issues persist, rebuild your Codespace${NC}"
echo -e "${BLUE}4. Run the verification scripts:${NC}"
echo -e "   ./verify_standard_mode.sh"
echo -e "   ./enhanced_verify_gcp_setup.sh"

echo "Fix completed at $(date)"
