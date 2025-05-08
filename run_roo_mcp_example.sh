#!/bin/bash
# run_roo_mcp_example.sh
#
# This script runs the Roo-MCP integration example with proper environment setup.
# It handles dependencies, environment variables, and provides clear output.

set -e  # Exit on error

# ANSI color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "======================================================"
echo "  Roo-MCP Integration Example Runner"
echo "======================================================"
echo -e "${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher is required.${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}Using Python $PYTHON_VERSION${NC}"

# Create and activate virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Run setup script if it exists
if [ -f "setup_roo_mcp.py" ]; then
    echo -e "${YELLOW}Running setup script...${NC}"
    python3 setup_roo_mcp.py
fi

# Set environment variables
export PYTHONPATH=$(pwd)
export MCP_SERVER_HOST=${MCP_SERVER_HOST:-localhost}
export MCP_SERVER_PORT=${MCP_SERVER_PORT:-8000}

# Check if the example script exists
if [ ! -f "examples/roo_mcp_integration_robust.py" ]; then
    echo -e "${RED}Error: Example script not found.${NC}"
    echo "Please make sure examples/roo_mcp_integration_robust.py exists."
    exit 1
fi

# Run the example script
echo -e "${YELLOW}Running Roo-MCP integration example...${NC}"
echo -e "${BLUE}=====================================================${NC}"
python3 examples/roo_mcp_integration_robust.py

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${BLUE}=====================================================${NC}"
    echo -e "${GREEN}Roo-MCP integration example completed successfully!${NC}"
    
    # Check if log file exists
    if [ -f "roo_mcp_integration.log" ]; then
        echo -e "${YELLOW}Log file created: roo_mcp_integration.log${NC}"
    fi
else
    echo -e "${BLUE}=====================================================${NC}"
    echo -e "${RED}Roo-MCP integration example failed.${NC}"
    echo "Please check the error messages above."
fi

# Deactivate virtual environment
deactivate

echo -e "${BLUE}=====================================================${NC}"