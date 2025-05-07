#!/bin/bash
# setup_local.sh
# Simplified script to set up the local environment for AI Orchestra project

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    "PHASE")
      echo -e "\n${YELLOW}========== ${message} ==========${NC}\n"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if a command exists
check_command() {
  if ! command -v $1 &> /dev/null; then
    log "ERROR" "$1 is required but not installed. Please install it and try again."
    exit 1
  fi
}

# Check prerequisites
check_prerequisites() {
  log "INFO" "Checking prerequisites..."
  
  # Check for required commands
  check_command "python3"
  check_command "pip"
  
  log "SUCCESS" "Prerequisites check passed"
}

# Set up Python environment
setup_python_environment() {
  log "PHASE" "SETTING UP PYTHON ENVIRONMENT"
  
  # Check if Poetry is installed
  if command -v poetry &> /dev/null; then
    log "INFO" "Poetry is installed, using it for dependency management"
    
    # Install dependencies with Poetry
    log "INFO" "Installing dependencies with Poetry..."
    poetry install --no-interaction
    
    log "SUCCESS" "Python environment set up with Poetry"
  else
    log "WARN" "Poetry is not installed, falling back to pip"
    
    # Create virtual environment
    log "INFO" "Creating virtual environment..."
    python3 -m venv .venv
    
    # Activate virtual environment
    log "INFO" "Activating virtual environment..."
    source .venv/bin/activate
    
    # Install dependencies with pip
    log "INFO" "Installing dependencies with pip..."
    pip install -r vertex_ai_requirements.txt
    pip install fastapi uvicorn pydantic python-dotenv
    
    log "SUCCESS" "Python environment set up with pip"
  fi
}

# Create necessary directories
create_directories() {
  log "PHASE" "CREATING NECESSARY DIRECTORIES"
  
  # Create directories if they don't exist
  log "INFO" "Creating necessary directories..."
  mkdir -p packages/api
  
  log "SUCCESS" "Directories created"
}

# Set up environment variables
setup_environment_variables() {
  log "PHASE" "SETTING UP ENVIRONMENT VARIABLES"
  
  # Check if .env file exists
  if [ ! -f .env ]; then
    log "INFO" "Creating .env file from .env.example..."
    if [ -f .env.example ]; then
      cp .env.example .env
      log "SUCCESS" ".env file created from .env.example"
    else
      log "WARN" ".env.example file not found, creating default .env file..."
      cat > .env << EOF
# Environment variables for AI Orchestra project
# Local development configuration

# Basic settings
ENVIRONMENT=dev
DEBUG=true

# GCP settings
PROJECT_ID=cherry-ai-project
REGION=us-central1

# Vertex AI settings
VERTEX_LOCATION=us-central1

# API settings
API_PREFIX=/api
PORT=8080

# Security settings
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
EOF
      log "SUCCESS" "Default .env file created"
    fi
  else
    log "INFO" ".env file already exists"
  fi
  
  log "SUCCESS" "Environment variables set up"
}

# Run the application
run_application() {
  log "PHASE" "RUNNING THE APPLICATION"
  
  # Get the port from .env or use default
  PORT=$(grep -oP 'PORT=\K[0-9]+' .env 2>/dev/null || echo "8000")
  
  log "INFO" "Starting AI Orchestra API on port ${PORT}..."
  log "INFO" "API will be available at http://localhost:${PORT}"
  log "INFO" "Press Ctrl+C to stop the server"
  
  # Run the application
  if command -v poetry &> /dev/null; then
    # Run with Poetry
    poetry run uvicorn packages.api.main:app --reload --host 0.0.0.0 --port "${PORT}"
  else
    # Run with activated virtual environment
    uvicorn packages.api.main:app --reload --host 0.0.0.0 --port "${PORT}"
  fi
}

# Main function
main() {
  log "INFO" "Starting local setup for AI Orchestra project..."
  
  # Check prerequisites
  check_prerequisites
  
  # Create necessary directories
  create_directories
  
  # Set up Python environment
  setup_python_environment
  
  # Set up environment variables
  setup_environment_variables
  
  # Run the application
  run_application
  
  log "SUCCESS" "Local setup completed successfully!"
}

# Execute main function
main