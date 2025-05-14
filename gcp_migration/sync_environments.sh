#!/bin/bash
# AI Orchestra Environment Synchronization
# Shell wrapper for environment_sync.py that provides easy synchronization
# between GitHub Codespaces and GCP Cloud Workstations

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default paths
CODESPACES_PATH="${PROJECT_ROOT}"
GCP_PATH="${PROJECT_ROOT}"
SYNC_SCRIPT="${SCRIPT_DIR}/environment_sync.py"
STATUS_FILE="${PROJECT_ROOT}/environment_sync_status.json"

# Default mode
MODE="bidirectional"

# Colors for formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage information
print_usage() {
  echo -e "${GREEN}AI Orchestra Environment Synchronization${NC}"
  echo
  echo "Usage: $0 [command] [options]"
  echo
  echo "Commands:"
  echo "  bidirectional     Sync in both directions (default)"
  echo "  to-gcp            Sync from Codespaces to GCP Workstation"
  echo "  to-codespaces     Sync from GCP Workstation to Codespaces"
  echo "  status            Show synchronization status"
  echo
  echo "Options:"
  echo "  --codespaces-dir  Path to GitHub Codespaces directory"
  echo "  --gcp-dir         Path to GCP Cloud Workstation directory"
  echo "  --status-file     Path to save synchronization status"
  echo "  --help            Show this help message"
  echo
  echo "Examples:"
  echo "  $0 bidirectional"
  echo "  $0 to-gcp --gcp-dir=/path/to/gcp/workstation"
  echo "  $0 status"
  echo
}

# Check if Python is available
check_python() {
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found in PATH${NC}"
    exit 1
  fi
}

# Check if environment_sync.py exists and is executable
check_sync_script() {
  if [ ! -f "$SYNC_SCRIPT" ]; then
    echo -e "${RED}Error: Sync script not found: $SYNC_SCRIPT${NC}"
    exit 1
  fi

  if [ ! -x "$SYNC_SCRIPT" ]; then
    echo -e "${YELLOW}Warning: Sync script is not executable. Attempting to make it executable...${NC}"
    chmod +x "$SYNC_SCRIPT"
  fi
}

# Detect current environment type
detect_environment() {
  if [ -n "$CODESPACES" ] && [ "$CODESPACES" = "true" ]; then
    echo "codespaces"
    return
  fi

  if [ -n "$CLOUD_WORKSTATIONS_ENVIRONMENT" ]; then
    echo "gcp-workstation"
    return
  fi

  # Try to detect based on files
  if [ -f "${PROJECT_ROOT}/.codespaces" ] || [ -d "${PROJECT_ROOT}/.codespaces" ]; then
    echo "codespaces"
    return
  fi

  if [ -f "${PROJECT_ROOT}/.gcp-workstation" ] || [ -d "${PROJECT_ROOT}/.gcp-workstation" ]; then
    echo "gcp-workstation"
    return
  fi

  echo "unknown"
}

# Set default directories based on environment
set_default_directories() {
  ENV_TYPE=$(detect_environment)
  
  if [ "$ENV_TYPE" = "codespaces" ]; then
    echo -e "${BLUE}Detected GitHub Codespaces environment${NC}"
    # Ask the user for GCP directory if not specified
    if [ "$GCP_PATH" = "$PROJECT_ROOT" ]; then
      read -p "Enter GCP Cloud Workstation directory (default: $GCP_PATH): " user_gcp_path
      if [ -n "$user_gcp_path" ]; then
        GCP_PATH="$user_gcp_path"
      fi
    fi
  elif [ "$ENV_TYPE" = "gcp-workstation" ]; then
    echo -e "${BLUE}Detected GCP Cloud Workstation environment${NC}"
    # Ask the user for Codespaces directory if not specified
    if [ "$CODESPACES_PATH" = "$PROJECT_ROOT" ]; then
      read -p "Enter GitHub Codespaces directory (default: $CODESPACES_PATH): " user_codespaces_path
      if [ -n "$user_codespaces_path" ]; then
        CODESPACES_PATH="$user_codespaces_path"
      fi
    fi
  else
    echo -e "${YELLOW}Unable to detect environment type automatically${NC}"
    # Ask the user for both directories if not specified
    if [ "$CODESPACES_PATH" = "$PROJECT_ROOT" ]; then
      read -p "Enter GitHub Codespaces directory (default: $CODESPACES_PATH): " user_codespaces_path
      if [ -n "$user_codespaces_path" ]; then
        CODESPACES_PATH="$user_codespaces_path"
      fi
    fi
    if [ "$GCP_PATH" = "$PROJECT_ROOT" ]; then
      read -p "Enter GCP Cloud Workstation directory (default: $GCP_PATH): " user_gcp_path
      if [ -n "$user_gcp_path" ]; then
        GCP_PATH="$user_gcp_path"
      fi
    fi
  fi
}

# Create .env file if it doesn't exist (for environment variable syncing)
ensure_env_files() {
  if [ ! -f "${CODESPACES_PATH}/.env" ]; then
    echo -e "${YELLOW}Creating .env file in Codespaces directory${NC}"
    touch "${CODESPACES_PATH}/.env"
  fi
  
  if [ ! -f "${GCP_PATH}/.env" ]; then
    echo -e "${YELLOW}Creating .env file in GCP directory${NC}"
    touch "${GCP_PATH}/.env"
  fi
}

# Create .vscode directories if they don't exist (for VS Code settings sync)
ensure_vscode_directories() {
  if [ ! -d "${CODESPACES_PATH}/.vscode" ]; then
    echo -e "${YELLOW}Creating .vscode directory in Codespaces directory${NC}"
    mkdir -p "${CODESPACES_PATH}/.vscode"
  fi
  
  if [ ! -d "${GCP_PATH}/.vscode" ]; then
    echo -e "${YELLOW}Creating .vscode directory in GCP directory${NC}"
    mkdir -p "${GCP_PATH}/.vscode"
  fi
}

# Create environment markers to help with detection
create_environment_markers() {
  if [ ! -f "${CODESPACES_PATH}/.codespaces" ]; then
    echo -e "${YELLOW}Creating environment marker in Codespaces directory${NC}"
    touch "${CODESPACES_PATH}/.codespaces"
  fi
  
  if [ ! -f "${GCP_PATH}/.gcp-workstation" ]; then
    echo -e "${YELLOW}Creating environment marker in GCP directory${NC}"
    touch "${GCP_PATH}/.gcp-workstation"
  fi
}

# Parse command line arguments
parse_args() {
  # Parse command (first argument)
  if [ $# -gt 0 ]; then
    case "$1" in
      bidirectional|to-gcp|to-codespaces|status)
        MODE="$1"
        shift
        ;;
      --help)
        print_usage
        exit 0
        ;;
    esac
  fi
  
  # Parse options
  while [ $# -gt 0 ]; do
    case "$1" in
      --codespaces-dir)
        CODESPACES_PATH="$2"
        shift 2
        ;;
      --gcp-dir)
        GCP_PATH="$2"
        shift 2
        ;;
      --status-file)
        STATUS_FILE="$2"
        shift 2
        ;;
      --help)
        print_usage
        exit 0
        ;;
      *)
        echo -e "${RED}Error: Unknown option $1${NC}"
        print_usage
        exit 1
        ;;
    esac
  done
}

# Map mode to sync script mode
map_mode() {
  case "$MODE" in
    bidirectional)
      echo "bidirectional"
      ;;
    to-gcp)
      echo "codespaces-to-gcp"
      ;;
    to-codespaces)
      echo "gcp-to-codespaces"
      ;;
    status)
      echo "status"
      ;;
    *)
      echo "bidirectional"
      ;;
  esac
}

# Run the sync script
run_sync() {
  SYNC_MODE=$(map_mode)
  
  echo -e "${BLUE}Starting environment synchronization...${NC}"
  echo -e "Mode: ${GREEN}${SYNC_MODE}${NC}"
  echo -e "Codespaces directory: ${CODESPACES_PATH}"
  echo -e "GCP directory: ${GCP_PATH}"
  echo -e "Status file: ${STATUS_FILE}"
  echo
  
  # Run the sync script
  "$SYNC_SCRIPT" --mode="$SYNC_MODE" \
    --codespaces-dir="$CODESPACES_PATH" \
    --gcp-dir="$GCP_PATH" \
    --status-file="$STATUS_FILE"
  
  RESULT=$?
  
  if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}Synchronization completed successfully!${NC}"
  else
    echo -e "${RED}Synchronization failed with exit code $RESULT${NC}"
    echo -e "Check the log file for more details: environment_sync.log"
  fi
  
  return $RESULT
}

# Main function
main() {
  # Parse command line arguments
  parse_args "$@"
  
  # Check requirements
  check_python
  check_sync_script
  
  # Set default directories based on environment
  set_default_directories
  
  # Ensure necessary files and directories exist
  ensure_env_files
  ensure_vscode_directories
  create_environment_markers
  
  # Run the sync script
  run_sync
  
  return $?
}

# Run the main function
main "$@"