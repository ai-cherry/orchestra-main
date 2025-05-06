#!/bin/bash
# setup_ci_environment.sh - Configure CI environment consistently

set -e

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up CI environment...${NC}"

# Ensure Poetry configuration is consistent
./scripts/configure_poetry.sh

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
poetry install --with dev

# Verify Python version
PYTHON_VERSION=$(python --version)
echo -e "${GREEN}Using Python: ${PYTHON_VERSION}${NC}"

# Verify Poetry version
POETRY_VERSION=$(poetry --version)
echo -e "${GREEN}Using Poetry: ${POETRY_VERSION}${NC}"

# Run basic validation checks
echo -e "${YELLOW}Running basic validation checks...${NC}"
poetry run python -c "import sys; print(f'Python path: {sys.executable}')"
poetry run python -c "import fastapi, pydantic, google.cloud; print('Key dependencies imported successfully')"

echo -e "${GREEN}CI environment setup complete.${NC}"