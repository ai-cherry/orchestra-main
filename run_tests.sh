#!/bin/bash
# Script to run tests with coverage analysis

echo "Activating virtual environment..."
source .venv/bin/activate || echo "Failed to activate virtual environment. Make sure .venv exists."

echo "Installing pytest-cov if needed..."
pip install -q pytest-cov==4.1.0

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run tests
run_tests() {
    echo -e "${BLUE}Running $1 tests...${NC}"
    $2
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}$1 tests passed!${NC}"
    else
        echo -e "${RED}$1 tests failed!${NC}"
    fi
    echo ""
}

# Check command line arguments
if [ "$1" == "critical" ]; then
    echo -e "${YELLOW}Running only critical tests...${NC}"
    run_tests "Critical" "pytest -m critical -v"
    exit 0
elif [ "$1" == "specific" ] && [ -n "$2" ]; then
    echo -e "${YELLOW}Running specific test: $2${NC}"
    run_tests "Specific" "pytest $2 -v"
    exit 0
fi

# Run all tests with coverage
echo -e "${YELLOW}Running all tests with coverage analysis...${NC}"

# Header for coverage report
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}                     Coverage Analysis                            ${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Run tests with coverage
pytest tests/ --verbose --cov=core.orchestrator --cov=packages.shared --cov-report=term-missing

# Run tests for key modules
echo -e "\n${YELLOW}Checking specific modules coverage...${NC}"

# Check /interact endpoint
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}             Coverage for /interact endpoint                      ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/test_interaction.py --cov=core.orchestrator.src.api.endpoints.interaction -v

# Check persona loading
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for persona loading                          ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/core/config/test_loader.py --cov=core.orchestrator.src.config.loader -v

# Check memory manager
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for memory manager                           ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/shared/memory/ --cov=packages.shared.src.memory -v

# Check agent registration
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for agent registration                       ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/ --cov=core.orchestrator.src.agents -v

echo -e "\n${GREEN}Testing completed!${NC}"
echo -e "${YELLOW}If you see any low coverage areas, consider adding more tests to increase coverage.${NC}"
