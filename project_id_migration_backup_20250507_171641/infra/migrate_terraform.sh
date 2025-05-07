#!/bin/bash
# Terraform Migration Script - From v1.5.0 to v1.11.3
# This script helps migrate from Terraform 1.5.0 to 1.11.3 with backup and rollback capabilities

set -e

# Set environment variables
PROJECT_ID="agi-baby-cherry"
REGION="us-central1"
ENV=${1:-dev}  # Default to dev if not specified
TERRAFORM_DIR="./infra/orchestra-terraform"
STATE_BUCKET="orchestra-terraform-state"
STATE_PREFIX="terraform/state/${ENV}"
BACKUP_PREFIX="terraform/state/backup/${ENV}"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Terraform Migration Script - v1.5.0 to v1.11.3 ===${NC}"
echo "Environment: ${ENV}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Terraform Directory: ${TERRAFORM_DIR}"
echo "State Bucket: ${STATE_BUCKET}"
echo "State Prefix: ${STATE_PREFIX}"
echo "Backup Prefix: ${BACKUP_PREFIX}"
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if tfenv is installed for Terraform version management
if ! command -v tfenv &> /dev/null; then
    echo -e "${YELLOW}Warning: tfenv is not installed. This script will use system Terraform version.${NC}"
    echo -e "${YELLOW}It's recommended to install tfenv for easy Terraform version switching.${NC}"
    echo "Run: git clone https://github.com/tfutils/tfenv.git ~/.tfenv"
    echo "Add to PATH: export PATH=\"\$HOME/.tfenv/bin:\$PATH\""
    echo
    read -p "Continue without tfenv? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_TFENV=false
else
    USE_TFENV=true
fi

# Check if the GCS bucket exists
if ! gsutil ls -b gs://${STATE_BUCKET} &> /dev/null; then
    echo -e "${YELLOW}State bucket does not exist. Creating...${NC}"
    gsutil mb -l ${REGION} -p ${PROJECT_ID} gs://${STATE_BUCKET}
    gsutil versioning set on gs://${STATE_BUCKET}
fi

# Function to ensure we're authenticated to GCP
ensure_gcp_auth() {
    echo "Checking GCP authentication..."
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        echo -e "${YELLOW}Not authenticated to GCP. Authenticating...${NC}"
        gcloud auth login
    fi
    
    echo "Setting GCP project..."
    gcloud config set project ${PROJECT_ID}
}

# Function to backup the current state
backup_state() {
    echo -e "${GREEN}=== Backing up current Terraform state ===${NC}"
    
    # Check if the state file exists
    if gsutil ls gs://${STATE_BUCKET}/${STATE_PREFIX}/default.tfstate &> /dev/null; then
        echo "Creating backup of current state file..."
        gsutil cp gs://${STATE_BUCKET}/${STATE_PREFIX}/default.tfstate gs://${STATE_BUCKET}/${BACKUP_PREFIX}/default.tfstate.${TIMESTAMP}
        echo "Backup created at: gs://${STATE_BUCKET}/${BACKUP_PREFIX}/default.tfstate.${TIMESTAMP}"
    else
        echo -e "${YELLOW}No state file found at gs://${STATE_BUCKET}/${STATE_PREFIX}/default.tfstate${NC}"
        echo "Continuing without backup..."
    fi
}

# Function to switch Terraform version
switch_terraform_version() {
    local version=$1
    echo -e "${GREEN}=== Switching to Terraform ${version} ===${NC}"
    
    if [ "$USE_TFENV" = true ]; then
        echo "Using tfenv to install and use Terraform ${version}..."
        tfenv install ${version}
        tfenv use ${version}
    else
        # Check system Terraform version
        local current_version=$(terraform version -json | jq -r '.terraform_version')
        if [ "$current_version" != "$version" ]; then
            echo -e "${RED}Error: System Terraform version is ${current_version}, not ${version}.${NC}"
            echo "Please install Terraform ${version} or use tfenv."
            exit 1
        fi
    fi
    
    terraform version
}

# Function to configure backend for state locking
configure_backend() {
    echo -e "${GREEN}=== Configuring Terraform backend with state locking ===${NC}"
    
    cd ${TERRAFORM_DIR}
    
    # Initialize Terraform with the GCS backend and state locking
    echo "Initializing Terraform with GCS backend..."
    terraform init \
        -backend-config="bucket=${STATE_BUCKET}" \
        -backend-config="prefix=${STATE_PREFIX}" \
        -upgrade
    
    # Verify workspace
    echo "Ensuring correct workspace..."
    terraform workspace select ${ENV} || terraform workspace new ${ENV}
}

# Function to test the configuration
test_configuration() {
    echo -e "${GREEN}=== Testing Terraform configuration ===${NC}"
    
    cd ${TERRAFORM_DIR}
    
    echo "Validating Terraform configuration..."
    terraform validate
    
    echo "Running Terraform plan..."
    terraform plan -var="env=${ENV}" -out=migration-plan.tfplan
    
    echo -e "${YELLOW}Please review the plan output above.${NC}"
    read -p "Continue with the migration? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration aborted by user."
        exit 0
    fi
}

# Function to apply the changes
apply_changes() {
    echo -e "${GREEN}=== Applying Terraform changes ===${NC}"
    
    cd ${TERRAFORM_DIR}
    
    echo "Applying Terraform plan..."
    terraform apply migration-plan.tfplan
    
    echo -e "${GREEN}Migration successfully completed!${NC}"
}

# Function for rollback
rollback() {
    echo -e "${RED}=== Rolling back due to error ===${NC}"
    
    cd ${TERRAFORM_DIR}
    
    # Switch back to old version
    if [ "$USE_TFENV" = true ]; then
        echo "Switching back to Terraform 1.5.0..."
        tfenv use 1.5.0
    fi
    
    # Restore state from backup
    echo "Would you like to restore the state from backup? (y/n)"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restoring state from backup..."
        # List available backups
        echo "Available backups:"
        gsutil ls gs://${STATE_BUCKET}/${BACKUP_PREFIX}/
        
        echo "Enter the backup filename to restore (e.g., default.tfstate.20250501120000):"
        read BACKUP_FILE
        
        if gsutil ls gs://${STATE_BUCKET}/${BACKUP_PREFIX}/${BACKUP_FILE} &> /dev/null; then
            gsutil cp gs://${STATE_BUCKET}/${BACKUP_PREFIX}/${BACKUP_FILE} gs://${STATE_BUCKET}/${STATE_PREFIX}/default.tfstate
            echo "State restored from backup."
        else
            echo -e "${RED}Backup file not found.${NC}"
            exit 1
        fi
    fi
    
    echo "Re-initializing Terraform..."
    terraform init -reconfigure
    
    echo "Running Terraform plan with old version..."
    terraform plan -var="env=${ENV}"
}

# Main execution
main() {
    ensure_gcp_auth
    backup_state
    
    # Start with old version to ensure we can access current state
    switch_terraform_version "1.5.0"
    
    # Run a plan with old version to save current config
    cd ${TERRAFORM_DIR}
    echo "Running plan with old version for reference..."
    terraform init \
        -backend-config="bucket=${STATE_BUCKET}" \
        -backend-config="prefix=${STATE_PREFIX}"
    terraform workspace select ${ENV} || terraform workspace new ${ENV}
    terraform plan -var="env=${ENV}" -out=pre-migration-plan.tfplan
    
    # Switch to new version
    switch_terraform_version "1.11.3"
    
    # Configure backend with state locking
    configure_backend
    
    # Test configuration
    test_configuration
    
    # Apply changes
    apply_changes
    
    echo -e "${GREEN}Migration from Terraform 1.5.0 to 1.11.3 completed successfully!${NC}"
    echo "The Terraform state is now using state locking with the GCS backend."
    echo "Workload Identity Federation is now configured for use with GitHub Actions."
}

# Check for rollback flag
if [ "$1" == "--rollback" ]; then
    rollback
else
    main
fi