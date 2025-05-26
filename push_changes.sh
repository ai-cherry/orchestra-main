#!/bin/bash
# push_changes.sh - Script to commit and push changes to GitHub

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Pushing Changes to GitHub ===${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Add the changes
echo -e "${YELLOW}Adding changes...${NC}"
git add mcp_server/health_check.py
git add mcp_server/server.py
git add mcp_server/DEPLOYMENT_GUIDE.md

# Commit the changes
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "Add health check endpoints and deployment guide for MCP server"

# Push the changes
echo -e "${YELLOW}Pushing changes to GitHub...${NC}"
git push

echo -e "${GREEN}Changes pushed successfully!${NC}"
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Go to the GitHub repository in your browser"
echo -e "2. Click on the 'Actions' tab"
echo -e "3. Select the 'Deploy MCP Server' workflow"
echo -e "4. Click 'Run workflow'"
echo -e "5. Select the environment (dev, staging, or prod)"
echo -e "6. Click 'Run workflow'"
echo -e "${BLUE}=== Deployment Started ===${NC}"
