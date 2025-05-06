#!/bin/bash
# Script to enforce standard mode operation and prevent restricted mode
# This script runs on container startup to ensure consistent environment configuration

# Color output for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ENFORCING STANDARD MODE ===${NC}"

# Set critical environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# Add environment variables to ~/.bashrc for persistence
if [ -f ~/.bashrc ]; then
  # Remove any existing mode settings
  grep -v "USE_RECOVERY_MODE\|STANDARD_MODE\|VSCODE_DISABLE_WORKSPACE_TRUST\|DISABLE_WORKSPACE_TRUST" ~/.bashrc > ~/.bashrc.tmp
  mv ~/.bashrc.tmp ~/.bashrc
  
  # Add the environment variables
  cat << 'EOF' >> ~/.bashrc

# Orchestra mode control environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
EOF
  
  echo -e "${GREEN}✓ Environment variables added to ~/.bashrc${NC}"
fi

# Fix common filesystem issues
echo -e "${YELLOW}Fixing common filesystem issues...${NC}"

# Make all .sh files executable
echo -e "${YELLOW}Making scripts executable...${NC}"
find /workspaces/orchestra-main -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || echo -e "${RED}Failed to make scripts executable${NC}"

# Fix ownership issues (common in containerized environments)
echo -e "${YELLOW}Fixing file ownership if needed...${NC}"
if [ "$(id -u)" -eq 0 ]; then
  # Only attempt if we're running as root
  chown -R $(stat -c '%u:%g' /workspaces/orchestra-main 2>/dev/null || echo "1000:1000") /workspaces/orchestra-main 2>/dev/null || echo -e "${RED}Failed to fix ownership${NC}"
fi

# Update VS Code workspace trust settings in settings.json
mkdir -p /workspaces/orchestra-main/.vscode
if [ -f /workspaces/orchestra-main/.vscode/settings.json ]; then
  echo -e "${YELLOW}Updating existing .vscode/settings.json...${NC}"
  # Basic sed approach since jq may not be available
  sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' /workspaces/orchestra-main/.vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' /workspaces/orchestra-main/.vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' /workspaces/orchestra-main/.vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' /workspaces/orchestra-main/.vscode/settings.json 2>/dev/null
else
  echo -e "${YELLOW}Creating new .vscode/settings.json...${NC}"
  cat << EOF > /workspaces/orchestra-main/.vscode/settings.json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
fi
echo -e "${GREEN}✓ VS Code settings updated${NC}"

# Modify the force_standard_mode.py script to always run on import
if [ -f /workspaces/orchestra-main/force_standard_mode.py ]; then
  echo -e "${YELLOW}Updating force_standard_mode.py to run on import...${NC}"
  sed -i 's/if __name__ == "__main__":/# Always run when imported\npatch_module()\n\nif __name__ == "__main__":/' /workspaces/orchestra-main/force_standard_mode.py
  echo -e "${GREEN}✓ Modified force_standard_mode.py to run automatically${NC}"
fi

echo -e "${GREEN}=== STANDARD MODE ENFORCED SUCCESSFULLY ===${NC}"
echo -e "${YELLOW}If IDE still shows restricted mode, please run the following command:${NC}"
echo -e "${BLUE}code --disable-workspace-trust .${NC}"