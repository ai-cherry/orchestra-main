#!/bin/bash
# dev.sh - AI Orchestra Development Script
#
# This script provides streamlined commands for common development tasks:
# - Setting up the development environment
# - Starting the development server
# - Running tests
# - Deploying to Cloud Run
# - Viewing logs
# - Managing GCP resources

set -e  # Exit on error

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Default values
PROJECT_ROOT=$(pwd)
DEFAULT_PORT=8080
DEFAULT_HOST="0.0.0.0"
DEFAULT_REGION="us-west4"

# Check if running in Codespaces and set up GCP if needed
setup_gcp() {
    if [ -n "$CODESPACES" ] && [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
        echo -e "${BLUE}Setting up GCP authentication for Codespaces...${RESET}"
        if [ -f "./scripts/setup_gcp_codespaces.sh" ]; then
            bash ./scripts/setup_gcp_codespaces.sh
        else
            echo -e "${RED}Error: setup_gcp_codespaces.sh not found${RESET}"
            exit 1
        fi
    else
        # Check if we have GCP credentials
        if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
            echo -e "${YELLOW}Warning: No GCP credentials found. Some features may not work.${RESET}"
            echo "Set GOOGLE_APPLICATION_CREDENTIALS or GCP_MASTER_SERVICE_JSON to enable GCP features."
        fi
    fi
}

# Check if Poetry is installed
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo -e "${YELLOW}Poetry not found. Installing...${RESET}"
        curl -sSL https://install.python-poetry.org | python3 -
        echo -e "${GREEN}✓ Poetry installed${RESET}"
    else
        echo -e "${GREEN}✓ Poetry already installed${RESET}"
    fi
}

# Install dependencies
install_deps() {
    echo -e "${BLUE}Installing dependencies...${RESET}"
    poetry install
    echo -e "${GREEN}✓ Dependencies installed${RESET}"
}

# Start the development server
start_server() {
    local port=${1:-$DEFAULT_PORT}
    local host=${2:-$DEFAULT_HOST}
    
    echo -e "${BLUE}Starting development server on $host:$port...${RESET}"
    poetry run uvicorn app:app --host $host --port $port --reload
}

# Run tests
run_tests() {
    local path=${1:-.}
    
    echo -e "${BLUE}Running tests in $path...${RESET}"
    poetry run pytest $path -v
}

# Deploy to Cloud Run
deploy() {
    local service_name=${1:-"ai-orchestra"}
    local region=${2:-$DEFAULT_REGION}
    
    echo -e "${BLUE}Deploying to Cloud Run...${RESET}"
    
    # Check if we have GCP credentials
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
        echo -e "${RED}Error: No GCP credentials found. Cannot deploy.${RESET}"
        exit 1
    fi
    
    # Get project ID
    if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
        PROJECT_ID=$(echo $GCP_MASTER_SERVICE_JSON | grep -o '"project_id": "[^"]*' | cut -d'"' -f4)
    elif [ -n "$GOOGLE_CLOUD_PROJECT" ]; then
        PROJECT_ID=$GOOGLE_CLOUD_PROJECT
    elif [ -n "$GCP_PROJECT_ID" ]; then
        PROJECT_ID=$GCP_PROJECT_ID
    else
        echo -e "${RED}Error: Could not determine GCP project ID${RESET}"
        exit 1
    fi
    
    echo -e "${BLUE}Building container image...${RESET}"
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$service_name
    
    echo -e "${BLUE}Deploying to Cloud Run...${RESET}"
    gcloud run deploy $service_name \
        --image gcr.io/$PROJECT_ID/$service_name \
        --platform managed \
        --region $region \
        --allow-unauthenticated
    
    echo -e "${GREEN}✓ Deployed to Cloud Run${RESET}"
    
    # Get the URL
    SERVICE_URL=$(gcloud run services describe $service_name --platform managed --region $region --format 'value(status.url)')
    echo -e "${GREEN}Service URL: $SERVICE_URL${RESET}"
}

# View logs
view_logs() {
    local service_name=${1:-"ai-orchestra"}
    local region=${2:-$DEFAULT_REGION}
    
    echo -e "${BLUE}Viewing logs for $service_name...${RESET}"
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$service_name" --limit 50
}

# Create a new component
create_component() {
    local component_type=$1
    local component_name=$2
    
    if [ -z "$component_type" ] || [ -z "$component_name" ]; then
        echo -e "${RED}Error: Component type and name are required${RESET}"
        echo "Usage: ./dev.sh create [type] [name]"
        echo "Types: adapter, manager, model, storage, util"
        exit 1
    fi
    
    case $component_type in
        adapter)
            target_dir="mcp_server/adapters"
            template="adapter_template.py"
            ;;
        manager)
            target_dir="mcp_server/managers"
            template="manager_template.py"
            ;;
        model)
            target_dir="mcp_server/models"
            template="model_template.py"
            ;;
        storage)
            target_dir="mcp_server/storage"
            template="storage_template.py"
            ;;
        util)
            target_dir="mcp_server/utils"
            template="util_template.py"
            ;;
        *)
            echo -e "${RED}Error: Unknown component type: $component_type${RESET}"
            echo "Valid types: adapter, manager, model, storage, util"
            exit 1
            ;;
    esac
    
    # Create directory if it doesn't exist
    mkdir -p $target_dir
    
    # Create file from template or create a basic file
    target_file="$target_dir/${component_name}.py"
    
    if [ -f "templates/$template" ]; then
        # Use template
        sed "s/COMPONENT_NAME/$component_name/g" "templates/$template" > $target_file
    else
        # Create basic file
        echo "#!/usr/bin/env python3" > $target_file
        echo "\"\"\"" >> $target_file
        echo "${component_name}.py - ${component_type^} for AI Orchestra" >> $target_file
        echo "" >> $target_file
        echo "This module provides a ${component_type} implementation for the AI Orchestra project." >> $target_file
        echo "\"\"\"" >> $target_file
        echo "" >> $target_file
        echo "import logging" >> $target_file
        echo "from typing import Dict, List, Optional, Any" >> $target_file
        echo "" >> $target_file
        echo "logger = logging.getLogger(__name__)" >> $target_file
        echo "" >> $target_file
        echo "class ${component_name^}:" >> $target_file
        echo "    \"\"\"${component_name^} implementation for AI Orchestra.\"\"\"" >> $target_file
        echo "    " >> $target_file
        echo "    def __init__(self):" >> $target_file
        echo "        \"\"\"Initialize the ${component_name}.\"\"\"" >> $target_file
        echo "        pass" >> $target_file
    fi
    
    echo -e "${GREEN}✓ Created $component_type: $target_file${RESET}"
}

# Show help
show_help() {
    echo -e "${BOLD}AI Orchestra Development Script${RESET}"
    echo "Usage: ./dev.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  setup              Set up the development environment"
    echo "  start [port]       Start the development server (default port: $DEFAULT_PORT)"
    echo "  test [path]        Run tests (default: all tests)"
    echo "  deploy [name]      Deploy to Cloud Run"
    echo "  logs [name]        View Cloud Run logs"
    echo "  create [type] [name] Create a new component"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh setup     Set up the development environment"
    echo "  ./dev.sh start 8000 Start the server on port 8000"
    echo "  ./dev.sh test      Run all tests"
    echo "  ./dev.sh deploy    Deploy to Cloud Run"
    echo "  ./dev.sh create adapter my_adapter  Create a new adapter"
}

# Main function
main() {
    local command=$1
    shift  # Remove the command from the arguments
    
    case $command in
        setup)
            echo -e "${BOLD}Setting up development environment...${RESET}"
            setup_gcp
            check_poetry
            install_deps
            echo -e "${GREEN}${BOLD}Development environment set up successfully!${RESET}"
            ;;
        start)
            echo -e "${BOLD}Starting development server...${RESET}"
            start_server "$@"
            ;;
        test)
            echo -e "${BOLD}Running tests...${RESET}"
            run_tests "$@"
            ;;
        deploy)
            echo -e "${BOLD}Deploying to Cloud Run...${RESET}"
            deploy "$@"
            ;;
        logs)
            echo -e "${BOLD}Viewing logs...${RESET}"
            view_logs "$@"
            ;;
        create)
            echo -e "${BOLD}Creating new component...${RESET}"
            create_component "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown command: $command${RESET}"
            show_help
            exit 1
            ;;
    esac
}

# Run the script
if [ $# -eq 0 ]; then
    show_help
else
    main "$@"
fi