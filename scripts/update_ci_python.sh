#!/bin/bash
# update_ci_python.sh - Update CI/CD pipeline to use pyenv for Python version management

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Updating CI/CD pipeline to use pyenv for Python version management...${NC}"

# Make the scripts executable
chmod +x scripts/setup_python_env.sh
chmod +x scripts/setup_poetry_env.sh

# Create a .python-version file in the project root
echo "3.11.9" > .python-version

# Create a .tool-versions file for asdf compatibility
echo "python 3.11.9" > .tool-versions

# Create a directory for service-specific Python versions
mkdir -p .python-envs

echo -e "${GREEN}CI/CD pipeline update complete.${NC}"
echo -e "To use service-specific Python versions:"
echo -e "1. Run: ./scripts/setup_python_env.sh <service_name>"
echo -e "2. Run: ./scripts/setup_poetry_env.sh <service_name>"
echo -e "3. Activate: cd .python-envs/<service_name> && poetry shell"