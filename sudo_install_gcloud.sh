#!/bin/bash
# sudo_install_gcloud.sh
# Script to run install_gcloud.sh with sudo privileges

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

# Check if install_gcloud.sh exists
if [ ! -f install_gcloud.sh ]; then
  log "ERROR" "install_gcloud.sh not found. Please make sure it exists in the current directory."
  exit 1
fi

# Check if install_gcloud.sh is executable
if [ ! -x install_gcloud.sh ]; then
  log "WARN" "install_gcloud.sh is not executable. Making it executable..."
  chmod +x install_gcloud.sh
fi

# Run install_gcloud.sh with sudo
log "INFO" "Running install_gcloud.sh with sudo privileges..."
sudo ./install_gcloud.sh

log "SUCCESS" "Google Cloud SDK installation completed!"