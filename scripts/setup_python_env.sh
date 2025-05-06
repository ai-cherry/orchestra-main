#!/bin/bash
# setup_python_env.sh - Configure Python environment for specific services

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default Python version
DEFAULT_PYTHON_VERSION="3.11.9"

# Service-specific Python versions
declare -A SERVICE_PYTHON_VERSIONS=(
  ["core"]="3.11.9"
  ["ingestion"]="3.10.13"
  ["llm-test"]="3.11.9"
  ["phidata"]="3.11.9"
)

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
  echo -e "${RED}Error: pyenv is not installed.${NC}"
  exit 1
fi

# Function to setup Python environment for a specific service
setup_service_env() {
  local service=$1
  local python_version=${SERVICE_PYTHON_VERSIONS[$service]:-$DEFAULT_PYTHON_VERSION}
  
  echo -e "${YELLOW}Setting up Python ${python_version} for ${service}...${NC}"
  
  # Check if the Python version is installed
  if ! pyenv versions | grep -q $python_version; then
    pyenv install $python_version
  fi
  
  # Create a directory for the service if it doesn't exist
  mkdir -p .python-envs/$service
  
  # Set local Python version for the service
  cd .python-envs/$service
  pyenv local $python_version
  
  echo -e "${GREEN}Python ${python_version} active for ${service}${NC}"
  
  # Return to the original directory
  cd - > /dev/null
}

# Main execution
if [ $# -eq 0 ]; then
  echo "Usage: $0 <service_name>"
  echo "Available services: ${!SERVICE_PYTHON_VERSIONS[@]}"
  exit 1
fi

service=$1
setup_service_env $service