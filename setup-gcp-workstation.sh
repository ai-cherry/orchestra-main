#!/bin/bash
# setup-gcp-workstation.sh - Script to provision a Compute Engine VM workstation
# This script creates a VM instance and sets it up with the necessary tools
# Created for AI Orchestra project (cherry-ai-project)

# Exit on error
set -e

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
ZONE="us-central1-a"
MACHINE_TYPE="e2-standard-4"
INSTANCE_NAME="my-workstation"
SERVICE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
REPO_URL="https://github.com/ai-cherry/orchestra-main.git"

# Log function for consistent output
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

# Function to check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Function to check if the VM already exists
check_vm_exists() {
  log "INFO" "Checking if VM instance '$INSTANCE_NAME' already exists..."
  
  if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
    log "INFO" "VM instance '$INSTANCE_NAME' already exists"
    return 0
  else
    log "INFO" "VM instance '$INSTANCE_NAME' does not exist"
    return 1
  fi
}

# Function to create the VM instance
create_vm_instance() {
  log "INFO" "Creating VM instance '$INSTANCE_NAME'..."
  
  # Create the VM instance
  gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --service-account=$SERVICE_ACCOUNT \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image-project=debian-cloud,image-family=debian-11 \
    --metadata=startup-script="#!/bin/bash
# Update and install dependencies
apt-get update
apt-get install -y git python3-pip python3-venv curl

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l \$SHELL
gcloud init --console-only

# Clone the repository
git clone $REPO_URL /home/\$(whoami)/orchestra-main

# Set up Python environment
cd /home/\$(whoami)/orchestra-main
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry install

# Set up environment variables
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/home/\$(whoami)/service-account.json' >> /home/\$(whoami)/.bashrc
echo 'export CLOUDSDK_CORE_PROJECT=$PROJECT_ID' >> /home/\$(whoami)/.bashrc
echo 'export CLOUDSDK_CORE_ZONE=$ZONE' >> /home/\$(whoami)/.bashrc
"
  
  log "SUCCESS" "VM instance '$INSTANCE_NAME' created successfully"
}

# Function to copy service account key to the VM
copy_service_account_key() {
  log "INFO" "Copying service account key to VM instance..."
  
  # Check if service account key exists
  if [ ! -f "$HOME/.gcp/service-account.json" ]; then
    log "ERROR" "Service account key not found at $HOME/.gcp/service-account.json"
    log "INFO" "Please run ./setup-gcp.sh first to set up authentication"
    return 1
  fi
  
  # Copy the service account key to the VM
  gcloud compute scp $HOME/.gcp/service-account.json $INSTANCE_NAME:~/service-account.json --zone=$ZONE --project=$PROJECT_ID
  
  log "SUCCESS" "Service account key copied to VM instance"
}

# Function to verify the VM setup
verify_vm_setup() {
  log "INFO" "Verifying VM setup..."
  
  # Check if the VM is running
  local status=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --format="value(status)")
  
  if [ "$status" = "RUNNING" ]; then
    log "SUCCESS" "VM instance '$INSTANCE_NAME' is running"
  else
    log "ERROR" "VM instance '$INSTANCE_NAME' is not running (status: $status)"
    return 1
  fi
  
  # Test SSH connection
  log "INFO" "Testing SSH connection..."
  if gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="echo 'SSH connection successful'" &>/dev/null; then
    log "SUCCESS" "SSH connection successful"
  else
    log "WARN" "SSH connection failed. This might be because the VM is still starting up."
    log "INFO" "Try connecting later with: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
  fi
  
  log "SUCCESS" "VM setup verification completed"
}

# Function to delete the VM instance
delete_vm_instance() {
  log "INFO" "Deleting VM instance '$INSTANCE_NAME'..."
  
  # Check if the VM exists
  if check_vm_exists; then
    # Delete the VM instance
    gcloud compute instances delete $INSTANCE_NAME \
      --zone=$ZONE \
      --project=$PROJECT_ID \
      --quiet
    
    log "SUCCESS" "VM instance '$INSTANCE_NAME' deleted successfully"
  else
    log "WARN" "VM instance '$INSTANCE_NAME' does not exist, nothing to delete"
  fi
}

# Main function
main() {
  log "INFO" "Starting GCP workstation setup..."
  
  # Check if gcloud is installed
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI not found. Please install the Google Cloud SDK."
    exit 1
  fi
  
  # Check if we're authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    log "ERROR" "Not authenticated with GCP. Please run ./setup-gcp.sh first."
    exit 1
  fi
  
  # Check if we're deleting the VM
  if [ "$1" = "cleanup" ]; then
    delete_vm_instance
    exit 0
  fi
  
  # Check if the VM already exists
  if ! check_vm_exists; then
    # Create the VM instance
    create_vm_instance
  fi
  
  # Copy service account key to the VM
  copy_service_account_key
  
  # Verify the VM setup
  verify_vm_setup
  
  log "SUCCESS" "GCP workstation setup completed successfully!"
  log "INFO" "You can connect to your workstation with:"
  log "INFO" "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
  log "INFO" "To delete the workstation, run:"
  log "INFO" "  ./setup-gcp-workstation.sh cleanup"
}

# Run the main function with command-line arguments
main "$@"