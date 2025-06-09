#!/bin/bash
# Script to run tests with coverage analysis

echo "Activating virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv .venv
fi
source .venv/bin/activate || echo "Failed to activate virtual environment. Proceeding without it."

export PYTHONPATH=$(pwd):$PYTHONPATH

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
elif [ "$1" == "portkey" ]; then
    echo -e "${YELLOW}Running Portkey client tests...${NC}"
    run_tests "Portkey" "pytest tests/packages/shared/llm_client/test_portkey_client.py -v"
    exit 0
elif [ "$1" == "memory" ]; then
    echo -e "${YELLOW}Running memory tests...${NC}"
    run_tests "Memory" "pytest tests/shared/memory/ -v"
    exit 0
elif [ "$1" == "simple" ]; then
    echo -e "${YELLOW}Running all tests (simple mode, no coverage)...${NC}"
    run_tests "All" "pytest tests/ -v"
    exit 0
elif [ -n "$1" ]; then
    echo -e "${YELLOW}Running tests in path: $1${NC}"
    run_tests "Path" "pytest $1 -v"
    exit 0
fi

# Run all tests with coverage
echo -e "${YELLOW}Running all tests with coverage analysis...${NC}"

# Header for coverage report
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}                     Coverage Analysis                            ${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Run tests with coverage
pytest tests/ --verbose --cov=core.conductor --cov=packages.shared --cov-report=term-missing

# Run tests for key modules
echo -e "\n${YELLOW}Checking specific modules coverage...${NC}"

# Check /interact endpoint
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}             Coverage for /interact endpoint                      ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/test_interaction.py --cov=core.conductor.src.api.endpoints.interaction -v

# Check persona loading
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for persona loading                          ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/core/config/test_loader.py --cov=core.conductor.src.config.loader -v

# Check memory manager
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for memory manager                           ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/shared/memory/ --cov=packages.shared.src.memory -v

# Check agent registration
echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}            Coverage for agent registration                       ${NC}"
echo -e "${BLUE}==================================================================${NC}"
pytest tests/ --cov=core.conductor.src.agents -v

echo -e "\n${GREEN}Testing completed!${NC}"
echo -e "${YELLOW}If you see any low coverage areas, consider adding more tests to increase coverage.${NC}"

# Usage instructions
echo -e "${BLUE}Usage:${NC}"
echo -e "${BLUE}  ./run_tests.sh                # Full test suite with coverage"
echo -e "${BLUE}  ./run_tests.sh simple         # All tests, no coverage"
echo -e "${BLUE}  ./run_tests.sh critical       # Only tests marked as critical"
echo -e "${BLUE}  ./run_tests.sh specific path  # Run a specific test file"
echo -e "${BLUE}  ./run_tests.sh portkey        # Run Portkey client tests"
echo -e "${BLUE}  ./run_tests.sh memory         # Run memory tests"
echo -e "${BLUE}  ./run_tests.sh <path>         # Run tests in a specific path"
