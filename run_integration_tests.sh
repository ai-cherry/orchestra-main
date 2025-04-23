#!/bin/bash
# Script to run integration tests with real services

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   Running Integration Tests for Storage Backends ${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check for environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}Warning: GCP_PROJECT_ID not set. Firestore tests will be skipped.${NC}"
fi

if [ -z "$REDIS_HOST" ]; then
    echo -e "${YELLOW}Warning: REDIS_HOST not set. Redis tests will be skipped.${NC}"
fi

# Set environment variable to run integration tests
export RUN_INTEGRATION_TESTS=true

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Install dependencies if needed
if ! command -v pytest &> /dev/null; then
    echo -e "${BLUE}Installing pytest and dependencies...${NC}"
    pip install -r requirements-dev.txt
fi

# Run the tests
echo -e "${BLUE}Running integration tests...${NC}"
python -m pytest tests/integration/test_storage.py -v

# Store the exit code
EXIT_CODE=$?

# Print results
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All integration tests passed!${NC}"
else
    echo -e "${RED}Some integration tests failed.${NC}"
fi

echo -e ""
echo -e "${YELLOW}Note:${NC}"
echo -e "To run with real GCP Firestore and Redis, set these environment variables:"
echo -e "- ${BLUE}GCP_PROJECT_ID${NC}: Your Google Cloud project ID"
echo -e "- ${BLUE}GCP_SA_KEY_JSON${NC}: JSON string containing service account key (preferred)"
echo -e "- ${BLUE}GCP_SA_KEY_PATH${NC}: Path to service account key file (alternative)"
echo -e "- ${BLUE}REDIS_HOST${NC}: Redis host address"
echo -e "- ${BLUE}REDIS_PORT${NC}: Redis port (default: 6379)"
echo -e "- ${BLUE}REDIS_PASSWORD${NC}: Redis password (if required)"

exit $EXIT_CODE
