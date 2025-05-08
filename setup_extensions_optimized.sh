#!/bin/bash
# setup_extensions_optimized.sh - Performance-optimized VS Code extension management
# 
# This script implements a tiered approach to extension installation:
# 1. Critical extensions are installed immediately
# 2. Development extensions are installed next
# 3. AI extensions are installed after development extensions
# 4. Optional extensions are installed in the background
#
# This approach ensures that the most important extensions are available
# immediately, while less important extensions are installed in the background.

set -e

# Color definitions for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Performance-Optimized VS Code Extension Manager ===${NC}"

# Configuration
WORKSPACE_ROOT="/workspaces/orchestra-main"
EXTENSIONS_CONFIG="${WORKSPACE_ROOT}/extensions.json"
LOG_DIR="${WORKSPACE_ROOT}/logs"
INSTALL_LOG="${LOG_DIR}/extension_install.log"

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Load extension configuration
if [ ! -f "$EXTENSIONS_CONFIG" ]; then
    echo -e "${YELLOW}Extensions configuration not found at ${EXTENSIONS_CONFIG}.${NC}"
    echo -e "${YELLOW}Creating default configuration...${NC}"
    
    # Create default configuration
    cat > "$EXTENSIONS_CONFIG" << EOF
{
  "critical": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "googlecloudtools.cloudcode",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform"
  ],
  "development": [
    "charliermarsh.ruff",
    "ms-python.black-formatter"
  ],
  "ai": [
    "github.copilot"
  ],
  "optional": []
}
EOF
    echo -e "${GREEN}Created default configuration at ${EXTENSIONS_CONFIG}${NC}"
fi

# Check if VS Code CLI is available
if [ -z "$(which code)" ]; then
    echo -e "${YELLOW}VS Code CLI not available. Extensions will be installed via devcontainer.json only.${NC}"
    echo -e "${YELLOW}Run 'python ${WORKSPACE_ROOT}/update_devcontainer_extensions.py' to update devcontainer.json.${NC}"
    exit 0
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo -e "${YELLOW}Please install jq to continue.${NC}"
    exit 1
fi

# Function to install extensions with progress tracking
install_extensions() {
    local category=$1
    local extensions=$2
    local count=$(echo "$extensions" | jq '. | length')
    
    if [ "$count" -eq 0 ]; then
        echo -e "${YELLOW}No ${category} extensions to install.${NC}"
        return
    fi
    
    echo -e "${BLUE}Installing ${count} ${category} extensions...${NC}"
    
    # Install extensions sequentially to avoid potential conflicts
    for i in $(seq 0 $(($count - 1))); do
        extension=$(echo "$extensions" | jq -r ".[$i]")
        
        # Check if extension is already installed
        if code --list-extensions | grep -q "^${extension}$"; then
            echo -e "${GREEN}Extension ${extension} is already installed.${NC}"
        else
            echo -e "${YELLOW}Installing ${extension}...${NC}"
            code --install-extension "$extension" --force > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}${extension} installed successfully${NC}"
            else
                echo -e "${RED}Failed to install ${extension}${NC}"
            fi
        fi
        
        # Show progress
        percent=$(( 100 * (i + 1) / $count ))
        echo -e "${BLUE}Progress: ${percent}% ($(($i + 1))/${count})${NC}"
    done
    
    echo -e "${GREEN}Completed installation of ${category} extensions${NC}"
}

# Parse extensions.json
EXTENSIONS_JSON=$(cat "$EXTENSIONS_CONFIG")
CRITICAL_EXTENSIONS=$(echo "$EXTENSIONS_JSON" | jq '.critical')
DEVELOPMENT_EXTENSIONS=$(echo "$EXTENSIONS_JSON" | jq '.development')
AI_EXTENSIONS=$(echo "$EXTENSIONS_JSON" | jq '.ai')
OPTIONAL_EXTENSIONS=$(echo "$EXTENSIONS_JSON" | jq '.optional')

# Install critical extensions first (these are needed for basic functionality)
echo -e "${BLUE}=== Installing Critical Extensions ===${NC}"
install_extensions "critical" "$CRITICAL_EXTENSIONS"

# Install development extensions (these improve the development experience)
echo -e "${BLUE}=== Installing Development Extensions ===${NC}"
install_extensions "development" "$DEVELOPMENT_EXTENSIONS"

# Install AI extensions (these provide AI assistance)
echo -e "${BLUE}=== Installing AI Extensions ===${NC}"
install_extensions "AI" "$AI_EXTENSIONS"

# Install optional extensions in the background
if [ -n "$OPTIONAL_EXTENSIONS" ] && [ "$(echo "$OPTIONAL_EXTENSIONS" | jq '. | length')" -gt 0 ]; then
    echo -e "${YELLOW}Installing optional extensions in the background...${NC}"
    (
        echo "=== Optional Extensions Installation Log $(date) ===" >> "$INSTALL_LOG"
        install_extensions "optional" "$OPTIONAL_EXTENSIONS" >> "$INSTALL_LOG" 2>&1
        echo "=== Optional Extensions Installation Complete $(date) ===" >> "$INSTALL_LOG"
    ) &
    
    echo -e "${YELLOW}Optional extensions being installed in background${NC}"
    echo -e "${YELLOW}Check ${INSTALL_LOG} for details${NC}"
fi

echo -e "${GREEN}=== Extension setup complete ===${NC}"
echo -e "${BLUE}💡 Tip: If any extensions aren't working correctly, try reloading the window (Ctrl+Shift+P > Developer: Reload Window)${NC}"
