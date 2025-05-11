#!/bin/bash
# Run WIF Implementation
# This script helps run the WIF implementation tools

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   WIF Implementation Plan Runner       ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    echo "Please install pip3 and try again"
    exit 1
fi

# Check if requirements are installed
echo -e "${YELLOW}Checking requirements...${NC}"
if ! pip3 freeze | grep -q "fastapi"; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip3 install -r wif_implementation_requirements.txt
    echo -e "${GREEN}Requirements installed successfully${NC}"
else
    echo -e "${GREEN}Requirements already installed${NC}"
fi

# Create templates directory if it doesn't exist
if [ ! -d "templates" ]; then
    echo -e "${YELLOW}Creating templates directory...${NC}"
    mkdir -p templates
    echo -e "${GREEN}Templates directory created${NC}"
fi

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  web                Start the web interface"
    echo "  cli [PHASE]        Run the CLI with the specified phase"
    echo "  test               Run the tests"
    echo "  help               Show this help message"
    echo
    echo "Phases for CLI:"
    echo "  vulnerabilities    Address Dependabot vulnerabilities"
    echo "  migration          Run migration script"
    echo "  cicd               Update CI/CD pipelines"
    echo "  training           Train team members"
    echo "  all                Execute all phases (default)"
    echo
    echo "Examples:"
    echo "  $0 web             # Start the web interface"
    echo "  $0 cli vulnerabilities  # Run the vulnerabilities phase"
    echo "  $0 test            # Run the tests"
}

# Check command line arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    web)
        echo -e "${YELLOW}Starting web interface...${NC}"
        echo -e "${YELLOW}Open your browser and navigate to http://127.0.0.1:8000${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        python3 wif_implementation_web.py
        ;;
    cli)
        if [ $# -eq 1 ]; then
            echo -e "${YELLOW}Running CLI with default phase (all)...${NC}"
            python3 wif_implementation_cli.py
        else
            echo -e "${YELLOW}Running CLI with phase: $2...${NC}"
            python3 wif_implementation_cli.py --phase "$2"
        fi
        ;;
    test)
        echo -e "${YELLOW}Running tests...${NC}"
        if ! command -v pytest &> /dev/null; then
            echo -e "${YELLOW}Installing pytest...${NC}"
            pip3 install pytest pytest-cov
        fi
        pytest tests/
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"