#!/bin/bash
# setup_poetry_env.sh - Configure Poetry environment for specific services

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
  echo -e "${RED}Error: pyenv is not installed.${NC}"
  exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
  echo -e "${RED}Error: Poetry is not installed.${NC}"
  exit 1
fi

# Function to setup Poetry environment for a specific service
setup_poetry_env() {
  local service=$1
  local env_dir=".python-envs/$service"
  
  echo -e "${YELLOW}Setting up Poetry environment for ${service}...${NC}"
  
  # Check if the service environment exists
  if [ ! -d "$env_dir" ]; then
    echo -e "${RED}Error: Service environment not found. Run setup_python_env.sh first.${NC}"
    exit 1
  fi
  
  # Navigate to the service directory
  cd $env_dir
  
  # Get the Python path from pyenv
  PYTHON_PATH=$(pyenv which python)
  
  # Configure Poetry to use this Python version
  poetry env use $PYTHON_PATH
  
  # Create a symlink to the project root pyproject.toml
  ln -sf ../../../pyproject.toml .
  ln -sf ../../../poetry.lock .
  
  # Install dependencies
  echo -e "${YELLOW}Installing dependencies for ${service}...${NC}"
  poetry install --no-root
  
  echo -e "${GREEN}Poetry environment for ${service} is ready.${NC}"
  echo -e "To activate: cd .python-envs/${service} && poetry shell"
  
  # Return to the original directory
  cd - > /dev/null
}

# Main execution
if [ $# -eq 0 ]; then
  echo "Usage: $0 <service_name>"
  echo "Available services: core, ingestion, llm-test, phidata"
  exit 1
fi

service=$1
setup_poetry_env $service