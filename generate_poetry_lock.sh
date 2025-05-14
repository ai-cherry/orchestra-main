#!/bin/bash
# Script to generate a fresh poetry.lock file for admin-api service
# This addresses the error: "pyproject.toml changed significantly since poetry.lock was last generated"

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SERVICE_DIR="services/admin-api"

echo -e "${BLUE}${BOLD}Generating poetry.lock file for ${SERVICE_DIR}${NC}"

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Poetry is not installed. Installing it now...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Navigate to the service directory
cd "${SERVICE_DIR}" || { 
    echo -e "${RED}Error: Could not navigate to ${SERVICE_DIR}${NC}" 
    exit 1
}

echo -e "${YELLOW}Current directory: $(pwd)${NC}"

# Backup the existing lock file if it exists
if [ -f poetry.lock ]; then
    echo -e "${YELLOW}Backing up existing poetry.lock file...${NC}"
    mv poetry.lock poetry.lock.bak
    echo -e "${GREEN}Backup created at poetry.lock.bak${NC}"
fi

# Generate a fresh lock file
echo -e "${YELLOW}Generating fresh poetry.lock file...${NC}"
poetry lock

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully generated poetry.lock file!${NC}"
else
    echo -e "${RED}Failed to generate poetry.lock file${NC}"
    
    # Restore backup if available
    if [ -f poetry.lock.bak ]; then
        echo -e "${YELLOW}Restoring backup...${NC}"
        mv poetry.lock.bak poetry.lock
    fi
    
    exit 1
fi

echo -e "${BLUE}${BOLD}Lock file generation complete!${NC}"
echo -e "You can now proceed with the deployment."