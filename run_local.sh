#!/bin/bash
# run_local.sh - Script to run the AI cherry_ai API locally

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
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
  log "ERROR" "Poetry is not installed. Please install it and try again."
  log "INFO" "You can install Poetry by running: curl -sSL https://install.python-poetry.org | python3 -"
  exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
  log "WARN" ".env file not found. Creating from .env.example..."
  if [ -f .env.example ]; then
    cp .env.example .env
    log "SUCCESS" ".env file created from .env.example"
    log "WARN" "Please update the .env file with your configuration"
  else
    log "ERROR" ".env.example file not found. Please create a .env file manually."
    exit 1
  fi
fi

# Install dependencies if needed
log "INFO" "Checking dependencies..."
poetry install --no-interaction

# Run the application
log "INFO" "Starting AI cherry_ai API..."
log "INFO" "API will be available at http://localhost:8000"
log "INFO" "Press Ctrl+C to stop the server"

# Get the port from .env or use default
PORT=$(grep -oP 'PORT=\K[0-9]+' .env 2>/dev/null || echo "8000")

# Run the application with Poetry
poetry run uvicorn packages.api.main:app --reload --host 0.0.0.0 --port "${PORT}"
