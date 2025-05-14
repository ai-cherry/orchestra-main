#!/bin/bash
# fix_poetry_lock.sh - Fix Poetry lock file for AI Orchestra services
#
# This script fixes Poetry lock file issues that cause Docker build failures.
# It ensures the lock file matches the pyproject.toml file.
#
# Usage:
#   ./fix_poetry_lock.sh [SERVICE_DIR]
#
# Example:
#   ./fix_poetry_lock.sh services/admin-api

set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default service directory
SERVICE_DIR=${1:-"services/admin-api"}
POETRY_VERSION="1.8.2"  # Pin specific version for consistency

echo -e "${BLUE}${BOLD}Poetry Lock File Fix Tool${NC}"
echo -e "${BLUE}Fixing Poetry lock file for ${SERVICE_DIR}${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing...${NC}"
    pip install "poetry==${POETRY_VERSION}"
else
    # Check Poetry version and update if needed
    CURRENT_VERSION=$(poetry --version | grep -oP '\d+\.\d+\.\d+')
    if [ "$CURRENT_VERSION" != "$POETRY_VERSION" ]; then
        echo -e "${YELLOW}Updating Poetry to version ${POETRY_VERSION}...${NC}"
        pip install --upgrade "poetry==${POETRY_VERSION}"
    else
        echo -e "${GREEN}Poetry version ${POETRY_VERSION} already installed.${NC}"
    fi
fi

# Verify Poetry version
echo -e "${BLUE}Using Poetry version:${NC}"
poetry --version

# Navigate to service directory
if [ ! -d "$SERVICE_DIR" ]; then
    echo -e "${RED}Error: Directory ${SERVICE_DIR} does not exist.${NC}"
    echo "Please provide a valid service directory."
    exit 1
fi

cd "$SERVICE_DIR"
echo -e "${BLUE}Working in directory: $(pwd)${NC}"

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found in ${SERVICE_DIR}.${NC}"
    exit 1
fi

# Back up the existing lock file
if [ -f "poetry.lock" ]; then
    echo -e "${YELLOW}Backing up existing poetry.lock file...${NC}"
    cp poetry.lock poetry.lock.backup
    echo -e "${GREEN}Backup created at poetry.lock.backup${NC}"
fi

# Generate a new lock file
echo -e "${BLUE}Generating new poetry.lock file...${NC}"
poetry lock --no-interaction

# Verify the lock file was created
if [ -f "poetry.lock" ]; then
    echo -e "${GREEN}${BOLD}Lock file generated successfully!${NC}"
    echo -e "${YELLOW}Remember to commit the new lock file to your repository:${NC}"
    echo "  git add poetry.lock"
    echo "  git commit -m \"Update poetry.lock to match pyproject.toml\""
else
    echo -e "${RED}Error: Failed to generate lock file.${NC}"
    if [ -f "poetry.lock.backup" ]; then
        echo -e "${YELLOW}Restoring backup...${NC}"
        mv poetry.lock.backup poetry.lock
    fi
    exit 1
fi

echo -e "${BLUE}${BOLD}Lock file update complete.${NC}"
echo -e "${GREEN}You can now build your Docker images without lock file issues.${NC}"