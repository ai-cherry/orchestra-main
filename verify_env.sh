#!/bin/bash
# This script verifies the Python environment for the Orchestra project

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Verifying Python environment for Orchestra project${NC}"

# Setting PYTHONPATH
export PYTHONPATH=/workspaces/orchestra-main
echo -e "${GREEN}PYTHONPATH set to $PYTHONPATH${NC}"

# Define virtual environment path
VENV_DIR=".venv"
VENV_PATH="$PYTHONPATH/$VENV_DIR"

# Check for virtual environment and activate it if needed
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}Found virtual environment at $VENV_PATH${NC}"
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$VENV_PATH/bin/activate"
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}Using Python from virtual environment: $(which python)${NC}"
else
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Using system Python. This may cause issues.${NC}"
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}Using system Python: $(which python3)${NC}"
    echo -e "${RED}Please run ./setup.sh first to create a virtual environment.${NC}"
fi

echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Verify basic imports
echo -e "${YELLOW}\nVerifying critical package imports:${NC}"

# Function to test imports
verify_import() {
    echo -ne "Testing import of $1... "
    if [ -d "$VENV_PATH" ]; then
        if python -c "import $1" 2>/dev/null; then
            echo -e "${GREEN}OK${NC}"
            return 0
        else
            echo -e "${RED}FAILED${NC}"
            return 1
        fi
    else
        if python3 -c "import $1" 2>/dev/null; then
            echo -e "${GREEN}OK${NC}"
            return 0
        else
            echo -e "${RED}FAILED${NC}"
            return 1
        fi
    fi
}

# Check critical imports
IMPORT_FAILED=0
verify_import fastapi || IMPORT_FAILED=1
verify_import pydantic || IMPORT_FAILED=1
verify_import openai || IMPORT_FAILED=1
verify_import uvicorn || IMPORT_FAILED=1

if [ $IMPORT_FAILED -eq 1 ]; then
    echo -e "${RED}\nCRITICAL ERROR: Some package imports failed.${NC}"
    echo -e "${RED}Please run './setup.sh' to fix the environment.${NC}"
    exit 1
else
    echo -e "${GREEN}\nAll critical package imports successful!${NC}"
fi

# Run a basic pytest check
echo -e "${YELLOW}\nAttempting to run pytest discovery:${NC}"
if [ -d "$VENV_PATH" ]; then
    if python -m pytest tests/ --collect-only; then
        echo -e "${GREEN}\nTest discovery successful!${NC}"
    else
        echo -e "${RED}\nTest discovery failed.${NC}"
        echo -e "${RED}This may be due to missing test dependencies or configuration issues.${NC}"
        exit 1
    fi
else
    if python3 -m pytest tests/ --collect-only; then
        echo -e "${GREEN}\nTest discovery successful!${NC}"
    else
        echo -e "${RED}\nTest discovery failed.${NC}"
        echo -e "${RED}This may be due to missing test dependencies or configuration issues.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}\nEnvironment verification complete. Basic functionality appears to be working.${NC}"
echo -e "${YELLOW}Next steps:${NC}"
if [ -d "$VENV_PATH" ]; then
    echo -e "1. Run full tests: ${GREEN}python -m pytest tests/${NC}"
else
    echo -e "1. Create virtual environment: ${GREEN}./setup.sh${NC}"
    echo -e "2. Run full tests: ${GREEN}python -m pytest tests/${NC}"
fi
echo -e "3. Start the API server: ${GREEN}bash run_api.sh${NC}"
echo -e "4. Test endpoints via: ${GREEN}http://localhost:8000/docs${NC}"
