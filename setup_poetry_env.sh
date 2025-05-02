#!/bin/bash
# Poetry Environment Setup Script for Orchestra
# This script helps manage Poetry environments in development and containerized settings

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Poetry Environment Setup for Orchestra${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Poetry. Exiting.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Poetry installed successfully.${NC}"
else
    echo -e "${GREEN}Poetry is already installed.${NC}"
    poetry --version
fi

# Ensure Poetry creates virtual environments in-project for better IDE integration
echo -e "${YELLOW}Configuring Poetry to create virtual environments in-project...${NC}"
poetry config virtualenvs.in-project true
echo -e "${GREEN}Poetry configuration updated.${NC}"

# Install dependencies based on environment
if [ "$1" == "--production" ]; then
    echo -e "${YELLOW}Installing production dependencies only...${NC}"
    poetry install --without dev,search_tools,documents,finance,comms --with litellm,portkey,openrouter
elif [ "$1" == "--minimal" ]; then
    echo -e "${YELLOW}Installing minimal dependencies...${NC}"
    poetry install --only main --no-root
elif [ "$1" == "--llm" ]; then
    echo -e "${YELLOW}Installing LLM gateway dependencies...${NC}"
    poetry install --with litellm,portkey,openrouter --without dev,search_tools,documents,finance,comms
else
    echo -e "${YELLOW}Installing all dependencies including development tools...${NC}"
    poetry install --with dev,search_tools,documents,finance,comms,litellm,portkey,openrouter
fi

# Update the lock file if requested
if [ "$2" == "--update-lock" ]; then
    echo -e "${YELLOW}Updating Poetry lock file...${NC}"
    poetry lock --no-update
    echo -e "${GREEN}Poetry lock file updated.${NC}"
fi

# Check if virtual environment was created properly
if [ -d ".venv" ]; then
    echo -e "${GREEN}Virtual environment created at: .venv${NC}"
    echo -e "${YELLOW}Python interpreter path: $(poetry env info --path)/bin/python${NC}"
    
    # Verify key dependencies are installed
    echo -e "${YELLOW}Verifying key dependencies...${NC}"
    poetry run python -c "import fastapi, uvicorn, loguru; print('✓ Core dependencies available')" || 
        echo -e "${RED}Some core dependencies are missing. Try running this script again.${NC}"
else
    echo -e "${RED}Virtual environment not found in project directory.${NC}"
    echo -e "${YELLOW}It might be located at: $(poetry env info --path)${NC}"
    echo -e "${YELLOW}You may need to manually set VS Code's Python interpreter path.${NC}"
fi

echo -e "${GREEN}Poetry environment setup complete.${NC}"
echo -e "${BLUE}Usage:${NC}"
echo -e "  To activate the environment in your terminal: ${YELLOW}source \$(poetry env info --path)/bin/activate${NC}"
echo -e "  To run commands with Poetry: ${YELLOW}poetry run <command>${NC}"
echo -e "  To add dependencies: ${YELLOW}poetry add <package>${NC}"
