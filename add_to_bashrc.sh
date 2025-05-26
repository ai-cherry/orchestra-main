#!/bin/bash
# add_to_bashrc.sh
# Script to add the source_env_and_ensure_gcp.sh script to the .bashrc file

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

# Check if the script is already in .bashrc
if grep -q "source_env_and_ensure_gcp.sh" ~/.bashrc; then
  log "INFO" "source_env_and_ensure_gcp.sh is already in .bashrc"
else
  # Add the script to .bashrc
  log "INFO" "Adding source_env_and_ensure_gcp.sh to .bashrc..."

  # Add a comment to .bashrc
  echo "" >> ~/.bashrc
  echo "# Source environment variables and ensure GCP environment variables are set correctly" >> ~/.bashrc
  echo "if [ -f \$PWD/source_env_and_ensure_gcp.sh ]; then" >> ~/.bashrc
  echo "  source \$PWD/source_env_and_ensure_gcp.sh" >> ~/.bashrc
  echo "elif [ -f /workspaces/orchestra-main/source_env_and_ensure_gcp.sh ]; then" >> ~/.bashrc
  echo "  source /workspaces/orchestra-main/source_env_and_ensure_gcp.sh" >> ~/.bashrc
  echo "fi" >> ~/.bashrc

  log "SUCCESS" "source_env_and_ensure_gcp.sh added to .bashrc!"
fi

# Remove any existing gcloud_config.sh call from .bashrc
log "INFO" "Removing any existing gcloud_config.sh call from .bashrc..."
sed -i '/gcloud_config.sh/d' ~/.bashrc

log "SUCCESS" "Configuration complete!"
log "INFO" "The source_env_and_ensure_gcp.sh script will now run automatically when a new terminal is opened."
log "INFO" "You can also run it manually with: source ./source_env_and_ensure_gcp.sh"
