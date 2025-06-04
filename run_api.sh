#!/bin/bash
# Script to run the FastAPI app - Can run in STANDARD or RECOVERY mode

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
MODE="standard"  # Default to standard mode
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --recovery) MODE="recovery"; shift ;;
        --standard) MODE="standard"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

echo -e "${YELLOW}Starting cherry_ai API in ${MODE^^} MODE${NC}"

# Source environment variables from set_env.sh if it exists
if [ -f "/workspaces/cherry_ai-main/set_env.sh" ]; then
    echo -e "${GREEN}Loading environment variables from set_env.sh...${NC}"
    source /workspaces/cherry_ai-main/set_env.sh
fi

# Setting PYTHONPATH
export PYTHONPATH=/workspaces/cherry_ai-main

# Set mode based on parameter
if [ "$MODE" == "recovery" ]; then
    export USE_RECOVERY_MODE=true
    export STANDARD_MODE=false
    echo -e "${YELLOW}Running in RECOVERY MODE${NC}"
else
    export USE_RECOVERY_MODE=false
    export STANDARD_MODE=true
    echo -e "${GREEN}Running in STANDARD MODE${NC}"
fi

echo -e "${GREEN}Critical environment variables:${NC}"
echo -e "PYTHONPATH=$PYTHONPATH"
echo -e "USE_RECOVERY_MODE=$USE_RECOVERY_MODE"
echo -e "STANDARD_MODE=$STANDARD_MODE"

# Define virtual environment path
VENV_DIR=".venv"
VENV_PATH="$PYTHONPATH/$VENV_DIR"

# Check for virtual environment and activate it if needed
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}Found virtual environment at $VENV_PATH${NC}"
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}Using Python: $(which python)${NC}"
else
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    # Try to create it on-the-fly
    echo -e "${YELLOW}Attempting to create virtual environment now...${NC}"
    if [ -f "/workspaces/cherry_ai-main/fix_dependencies.sh" ]; then
        echo -e "${YELLOW}Running fix_dependencies.sh...${NC}"
        bash /workspaces/cherry_ai-main/fix_dependencies.sh
        if [ -d "$VENV_PATH" ]; then
            echo -e "${GREEN}Virtual environment created successfully.${NC}"
            source "$VENV_PATH/bin/activate"
        else
            echo -e "${RED}Failed to create virtual environment.${NC}"
            echo -e "${YELLOW}Running with system Python: $(which python3)${NC}"
        fi
    else
        echo -e "${YELLOW}Running with system Python: $(which python3)${NC}"
        echo -e "${RED}This may cause dependency issues. Run ./setup.sh first to create the virtual environment.${NC}"
    fi
fi

# Kill any existing processes running on port 8000
echo -e "${YELLOW}Checking for processes running on port 8000...${NC}"
# Try both lsof and fuser for port checking, as container environments may have different tools
PORT_PID=$(lsof -t -i:8000 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo -e "${YELLOW}Killing existing process on port 8000 (PID: $PORT_PID)...${NC}"
    kill -9 $PORT_PID
else
    # Alternative using fuser if lsof isn't available
    fuser -k 8000/tcp 2>/dev/null || true
fi

# Verify critical imports before starting
echo -e "${YELLOW}Checking critical imports before starting...${NC}"
IMPORT_FAILED=0
for package in fastapi pydantic openai uvicorn
do
    echo -ne "Testing import of $package... "
    if python -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        # Instead of just failing, try to fix the issue
        echo -e "${YELLOW}Attempting to install $package...${NC}"
        pip install $package
        if python -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}Successfully installed $package${NC}"
        else
            echo -e "${RED}Failed to install $package${NC}"
            IMPORT_FAILED=1
        fi
    fi
done

if [ $IMPORT_FAILED -eq 1 ]; then
    echo -e "${RED}Some required packages are missing!${NC}"
    echo -e "${YELLOW}Attempting to run fix_dependencies.sh...${NC}"
    if [ -f "/workspaces/cherry_ai-main/fix_dependencies.sh" ]; then
        bash /workspaces/cherry_ai-main/fix_dependencies.sh
        IMPORT_FAILED=0
        # Check imports again after running fix_dependencies.sh
        for package in fastapi pydantic openai uvicorn
        do
            if ! python -c "import $package" 2>/dev/null; then
                IMPORT_FAILED=1
                break
            fi
        done

        if [ $IMPORT_FAILED -eq 1 ]; then
            echo -e "${RED}Dependencies still missing after fix attempt. Continuing anyway...${NC}"
        else
            echo -e "${GREEN}Dependencies fixed successfully!${NC}"
        fi
    else
        echo -e "${RED}fix_dependencies.sh not found. Continuing anyway...${NC}"
    fi
fi

# ----- MODE SELECTION -----
# Only apply force_standard_mode patch if we're in standard mode
if [ "$MODE" == "standard" ]; then
    echo -e "${YELLOW}Applying standard mode patch...${NC}"
    if [ -f "/workspaces/cherry_ai-main/force_standard_mode.py" ]; then
        python /workspaces/cherry_ai-main/force_standard_mode.py
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Standard mode patch applied successfully.${NC}"
        else
            echo -e "${RED}Failed to apply standard mode patch.${NC}"
        fi
    else
        echo -e "${RED}force_standard_mode.py not found.${NC}"
    fi
else
    echo -e "${YELLOW}Skipping standard mode patch for recovery mode.${NC}"
fi

# Run the FastAPI app with the appropriate structure
echo -e "${GREEN}Starting FastAPI app - conductor API (${MODE^^} MODE)${NC}"
echo -e "${GREEN}Using Python: $(which python)${NC}"
echo -e "${GREEN}PYTHONPATH: $PYTHONPATH${NC}"
echo -e "${GREEN}USE_RECOVERY_MODE: $USE_RECOVERY_MODE${NC}"
echo -e "${GREEN}STANDARD_MODE: $STANDARD_MODE${NC}"

# Run with PYTHONPATH using the -m flag for better module resolution
PYTHONPATH=$PYTHONPATH python -c "import os; print('Python sees USE_RECOVERY_MODE=', os.environ.get('USE_RECOVERY_MODE', 'not set'))"

if [ "$MODE" == "recovery" ]; then
    PYTHONPATH=$PYTHONPATH python -m uvicorn core.conductor.src.main_simple:app --reload --host 0.0.0.0 --port 8000
else
    PYTHONPATH=$PYTHONPATH python -m uvicorn core.conductor.src.main:app --reload --host 0.0.0.0 --port 8000
fi
