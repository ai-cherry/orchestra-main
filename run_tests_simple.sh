#!/bin/bash
# Simple test runner with proper environment setup for Orchestra

# Define colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up test environment...${NC}"

# 1. Activate virtual environment
echo -e "Activating virtual environment..."
source .venv/bin/activate || {
    echo -e "${YELLOW}Failed to activate virtual environment. Creating a new one...${NC}"
    python -m venv .venv
    source .venv/bin/activate || { 
        echo -e "${YELLOW}Failed to create virtual environment. Proceeding without it.${NC}"
    }
}

# 2. Set PYTHONPATH to include the project root directory
echo -e "Setting PYTHONPATH to include the project root..."
export PYTHONPATH=$(pwd)
echo -e "PYTHONPATH=${PYTHONPATH}"

# 3. Check for pytest and install if needed
echo -e "Checking for pytest..."
if ! pip list | grep -q "pytest"; then
    echo -e "${YELLOW}Installing pytest...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# 4. Parse command line arguments
if [ "$1" == "specific" ] && [ -n "$2" ]; then
    echo -e "${YELLOW}Running specific test: $2${NC}"
    python -m pytest "$2" -v
    exit $?
elif [ "$1" == "critical" ]; then
    echo -e "${YELLOW}Running only critical tests...${NC}"
    python -m pytest tests/ -m critical -v
    exit $?
elif [ "$1" == "portkey" ]; then
    echo -e "${YELLOW}Running Portkey client tests...${NC}"
    python -m pytest tests/packages/shared/llm_client/test_portkey_client.py -v
    exit $?
elif [ "$1" == "memory" ]; then
    echo -e "${YELLOW}Running memory tests...${NC}"
    python -m pytest tests/shared/memory/ -v
    exit $?
elif [ -n "$1" ]; then
    echo -e "${YELLOW}Running tests in path: $1${NC}"
    python -m pytest "$1" -v
    exit $?
fi

# 5. Run all tests by default
echo -e "${YELLOW}Running all tests...${NC}"
python -m pytest tests/ -v

echo -e "\n${GREEN}Testing completed!${NC}"
