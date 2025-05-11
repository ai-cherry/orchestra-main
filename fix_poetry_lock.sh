#!/bin/bash
# fix_poetry_lock.sh - Script to fix Poetry dependency issues for MCP server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Poetry Dependency Issues for MCP Server ===${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry is not installed${NC}"
    echo -e "Please install Poetry first: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "mcp_server" ]; then
    echo -e "${RED}Error: mcp_server directory not found${NC}"
    echo -e "Please run this script from the root of the repository"
    exit 1
fi

# Step 1: Check if pyproject.toml exists in mcp_server directory
echo -e "${YELLOW}Step 1: Checking if pyproject.toml exists in mcp_server directory${NC}"
if [ ! -f "mcp_server/pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found in mcp_server directory${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pyproject.toml found in mcp_server directory${NC}"

# Step 2: Generate poetry.lock file
echo -e "\n${YELLOW}Step 2: Generating poetry.lock file${NC}"
cd mcp_server
if [ -f "poetry.lock" ]; then
    echo -e "  poetry.lock already exists, backing it up to poetry.lock.bak"
    mv poetry.lock poetry.lock.bak
fi

echo -e "  Running poetry lock --no-update"
if poetry lock --no-update; then
    echo -e "${GREEN}✓ poetry.lock generated successfully${NC}"
else
    echo -e "${RED}✗ Failed to generate poetry.lock${NC}"
    if [ -f "poetry.lock.bak" ]; then
        echo -e "  Restoring poetry.lock.bak"
        mv poetry.lock.bak poetry.lock
    fi
    exit 1
fi

# Step 3: Verify the lock file
echo -e "\n${YELLOW}Step 3: Verifying the lock file${NC}"
if poetry check; then
    echo -e "${GREEN}✓ poetry.lock is valid${NC}"
else
    echo -e "${RED}✗ poetry.lock is invalid${NC}"
    if [ -f "poetry.lock.bak" ]; then
        echo -e "  Restoring poetry.lock.bak"
        mv poetry.lock.bak poetry.lock
    fi
    exit 1
fi

# Step 4: Test installing dependencies
echo -e "\n${YELLOW}Step 4: Testing dependency installation${NC}"
if poetry install --no-root --dry-run; then
    echo -e "${GREEN}✓ Dependencies can be installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    if [ -f "poetry.lock.bak" ]; then
        echo -e "  Restoring poetry.lock.bak"
        mv poetry.lock.bak poetry.lock
    fi
    exit 1
fi

# Step 5: Clean up
echo -e "\n${YELLOW}Step 5: Cleaning up${NC}"
if [ -f "poetry.lock.bak" ]; then
    echo -e "  Removing poetry.lock.bak"
    rm poetry.lock.bak
fi
cd ..

echo -e "\n${BLUE}=== Poetry Dependency Issues Fixed ===${NC}"
echo -e "The poetry.lock file has been generated successfully."
echo -e "You can now commit this file to your repository:"
echo -e "  git add mcp_server/poetry.lock"
echo -e "  git commit -m \"Add poetry.lock file for mcp_server\""
echo -e "  git push"