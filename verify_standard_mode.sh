#!/bin/bash

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  VERIFYING STANDARD MODE AND WORKSPACE TRUST SETTINGS${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Check environment variables
echo -e "\n${BLUE}Checking environment variables:${NC}"

if [ "$VSCODE_DISABLE_WORKSPACE_TRUST" = "true" ]; then
    echo -e "${GREEN}✓ VSCODE_DISABLE_WORKSPACE_TRUST is set to true${NC}"
else
    echo -e "${RED}✗ VSCODE_DISABLE_WORKSPACE_TRUST is not set to true (current value: $VSCODE_DISABLE_WORKSPACE_TRUST)${NC}"
fi

if [ "$STANDARD_MODE" = "true" ]; then
    echo -e "${GREEN}✓ STANDARD_MODE is set to true${NC}"
else
    echo -e "${RED}✗ STANDARD_MODE is not set to true (current value: $STANDARD_MODE)${NC}"
fi

if [ "$DISABLE_WORKSPACE_TRUST" = "true" ]; then
    echo -e "${GREEN}✓ DISABLE_WORKSPACE_TRUST is set to true${NC}"
else
    echo -e "${RED}✗ DISABLE_WORKSPACE_TRUST is not set to true (current value: $DISABLE_WORKSPACE_TRUST)${NC}"
fi

if [ "$USE_RECOVERY_MODE" = "false" ]; then
    echo -e "${GREEN}✓ USE_RECOVERY_MODE is set to false${NC}"
elif [ -z "$USE_RECOVERY_MODE" ]; then
    echo -e "${YELLOW}! USE_RECOVERY_MODE is not set${NC}"
else
    echo -e "${RED}✗ USE_RECOVERY_MODE is not set to false (current value: $USE_RECOVERY_MODE)${NC}"
fi

# Check for VS Code settings
echo -e "\n${BLUE}Checking VS Code settings:${NC}"

# Check .vscode/settings.json
if [ -f .vscode/settings.json ]; then
    echo -e "${GREEN}✓ .vscode/settings.json exists${NC}"
    
    # Check for workspace trust settings
    if grep -q "\"security.workspace.trust.enabled\": false" .vscode/settings.json; then
        echo -e "${GREEN}✓ Workspace trust is disabled in settings.json${NC}"
    else
        echo -e "${RED}✗ Workspace trust is not properly disabled in settings.json${NC}"
    fi
else
    echo -e "${RED}✗ .vscode/settings.json does not exist${NC}"
fi

# Check devcontainer.json
if [ -f .devcontainer/devcontainer.json ]; then
    echo -e "${GREEN}✓ .devcontainer/devcontainer.json exists${NC}"
    
    # Check for workspace trust settings
    if grep -q "\"security.workspace.trust.enabled\": false" .devcontainer/devcontainer.json; then
        echo -e "${GREEN}✓ Workspace trust is disabled in devcontainer.json${NC}"
    else
        echo -e "${RED}✗ Workspace trust is not properly disabled in devcontainer.json${NC}"
    fi
else
    echo -e "${RED}✗ .devcontainer/devcontainer.json does not exist${NC}"
fi

# Check for recovery container
echo -e "\n${BLUE}Checking for recovery container:${NC}"
if grep -q "recovery container" ../.codespaces/.persistedshare/creation.log 2>/dev/null; then
    echo -e "${YELLOW}! Codespace was created using a recovery container${NC}"
    echo -e "${YELLOW}! This may indicate that your original container configuration failed to build${NC}"
else
    echo -e "${GREEN}✓ No recovery container detected${NC}"
fi

# Check for restricted mode references
echo -e "\n${BLUE}Checking for restricted mode references:${NC}"
if grep -q -i "restricted mode" ../.codespaces/.persistedshare/creation.log 2>/dev/null; then
    echo -e "${YELLOW}! References to restricted mode found in creation log${NC}"
    grep -i "restricted mode" ../.codespaces/.persistedshare/creation.log | head -3 2>/dev/null
else
    echo -e "${GREEN}✓ No explicit restricted mode references in creation log${NC}"
fi

echo -e "\n${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${GREEN}  STANDARD MODE VERIFICATION COMPLETE${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

echo -e "\n${YELLOW}If VS Code still shows restricted mode after these checks, try:${NC}"
echo -e "${BLUE}1. Run 'source ~/.bashrc' to ensure environment variables are set${NC}"
echo -e "${BLUE}2. Reload VS Code window (Command Palette > Developer: Reload Window)${NC}"
echo -e "${BLUE}3. If issues persist, try rebuilding the Codespace${NC}"
