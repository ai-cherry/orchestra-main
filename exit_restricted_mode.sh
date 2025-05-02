#!/bin/bash
# Script to exit restricted mode and clean up workspace
# This will help restore your environment to a normal state

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Exiting Restricted Mode and Cleaning Workspace${NC}"

# Check if we're in a Codespace environment
if [ -z "$CODESPACES" ]; then
  echo -e "${YELLOW}Note: This doesn't appear to be a GitHub Codespace environment.${NC}"
fi

# Check current mode and permissions
echo -e "${YELLOW}Checking current environment state...${NC}"
if [ -w "/workspaces/orchestra-main" ]; then
  echo -e "${GREEN}Write permissions to workspace directory confirmed.${NC}"
else
  echo -e "${RED}Restricted write permissions detected. This script may not work fully.${NC}"
  echo -e "${YELLOW}You may need to rebuild your container from the Command Palette.${NC}"
fi

# Try to restore normal mode
echo -e "${YELLOW}Attempting to restore normal execution mode...${NC}"

# Reset environment variables that might be causing issues
if [ -n "$USE_RECOVERY_MODE" ]; then
  echo -e "${YELLOW}Found USE_RECOVERY_MODE environment variable. Unsetting...${NC}"
  unset USE_RECOVERY_MODE
fi

# Function to fix common filesystem issues
fix_filesystem_issues() {
  echo -e "${YELLOW}Fixing common filesystem issues...${NC}"
  
  # Make all .sh files executable
  echo -e "${YELLOW}Making scripts executable...${NC}"
  find /workspaces/orchestra-main -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || echo -e "${RED}Failed to make scripts executable${NC}"
  
  # Fix ownership issues (common in containerized environments)
  echo -e "${YELLOW}Fixing file ownership...${NC}"
  if [ "$(id -u)" -eq 0 ]; then
    # Only attempt if we're running as root
    chown -R $(stat -c '%u:%g' /workspaces/orchestra-main) /workspaces/orchestra-main 2>/dev/null || echo -e "${RED}Failed to fix ownership${NC}"
  fi
  
  echo -e "${GREEN}Filesystem issues addressed.${NC}"
}

# Clean up temporary files that might be causing issues
clean_temp_files() {
  echo -e "${YELLOW}Cleaning up temporary files...${NC}"
  find /workspaces/orchestra-main -name "*.tmp" -type f -delete 2>/dev/null
  find /workspaces/orchestra-main -name "*.lock" -type f -not -name "poetry.lock" -delete 2>/dev/null
  find /workspaces/orchestra-main -name ".coverage*" -delete 2>/dev/null
  echo -e "${GREEN}Temporary files cleaned.${NC}"
}

# Reset Docker if available
reset_docker() {
  echo -e "${YELLOW}Checking Docker status...${NC}"
  if command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker command found. Attempting to restart Docker service...${NC}"
    service docker restart 2>/dev/null || echo -e "${RED}Failed to restart Docker service${NC}"
    echo -e "${GREEN}Docker reset attempt completed.${NC}"
  else
    echo -e "${YELLOW}Docker command not found. Skipping Docker reset.${NC}"
  fi
}

# Run all cleanup functions
fix_filesystem_issues
clean_temp_files
reset_docker

echo -e "${GREEN}Cleanup completed. To fully exit restricted mode, you likely need to:${NC}"
echo -e "${BLUE}1. Open VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)${NC}"
echo -e "${BLUE}2. Type and select 'Codespaces: Rebuild Container'${NC}"
echo -e "${BLUE}3. Wait for the rebuild to complete${NC}"
echo -e "${YELLOW}This will apply all the configuration changes we've made to fix the issues.${NC}"