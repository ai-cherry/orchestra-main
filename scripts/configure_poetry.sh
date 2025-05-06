#!/bin/bash
# configure_poetry.sh - Ensure consistent Poetry configuration across environments

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
  echo -e "${RED}Error: Poetry is not installed.${NC}"
  exit 1
fi

echo -e "${YELLOW}Configuring Poetry with standard settings...${NC}"

# Configure Poetry
poetry config virtualenvs.in-project true
poetry config virtualenvs.create true
poetry config installer.parallel true
poetry config cache-dir "${POETRY_HOME:-$HOME/.poetry}/cache"

# Display configuration
echo -e "${GREEN}Poetry configuration:${NC}"
poetry config --list

echo -e "${GREEN}Poetry configuration complete.${NC}"