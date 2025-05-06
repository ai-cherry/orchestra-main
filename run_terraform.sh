#!/bin/bash
# ======================================
# Orchestra Terraform Runner
# ======================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"
ENV="${1:-dev}"  # Default to dev environment if not specified

# Validate environment
if [ "$ENV" != "dev" ] && [ "$ENV" != "stage" ] && [ "$ENV" != "prod" ]; then
    echo -e "${RED}Error: Invalid environment. Must be 'dev', 'stage', or 'prod'.${NC}"
    exit 1
fi

# Check if production and required files exist
if [ "$ENV" == "prod" ]; then
    if [ ! -f "infra/prod.tfvars" ]; then
        echo -e "${RED}Error: infra/prod.tfvars file not found.${NC}"
        echo -e "${RED}Please create the production Terraform variables file first.${NC}"
        exit 1
    fi
else
    # For non-production environments, use standard terraform.tfvars
    TFVARS_ARG="-var=\"env=${ENV}\""
fi

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}${BOLD}   Orchestra Terraform - $ENV environment   ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Terraform directory
TERRAFORM_DIR="infra/orchestra-terraform"

# Make sure FIGMA_PAT is set (default to empty string if not)
export FIGMA_PAT="${FIGMA_PAT:-}"

# Check for and mount Google Cloud credentials
GCLOUD_ADC_PATH="/home/vscode/.config/gcloud/application_default_credentials.json"
if [ ! -f "$GCLOUD_ADC_PATH" ]; then
    echo -e "${YELLOW}Google Cloud credentials not found at $GCLOUD_ADC_PATH. Attempting to authenticate...${NC}"
    gcloud auth application-default login
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Google Cloud authentication failed. Please authenticate manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Google Cloud authentication successful. Credentials saved to $GCLOUD_ADC_PATH.${NC}"
fi

GCLOUD_VOLUME_MOUNT="-v $GCLOUD_ADC_PATH:/root/.config/gcloud/application_default_credentials.json"
echo -e "${YELLOW}Mounting Google Cloud credentials from $GCLOUD_ADC_PATH${NC}"

# Build Docker image
echo -e "${YELLOW}Building Terraform Docker image...${NC}"
docker build -t terraform-orchestra -f ${TERRAFORM_DIR}/Dockerfile.terraform .

# Run Terraform command in the container
echo -e "${YELLOW}=== Running Terraform $TERRAFORM_ACTION ===${NC}"

# Add special handling for init and workspace commands
if [ "$TERRAFORM_ACTION" == "init" ]; then
    # Always run init first
    docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
        -e FIGMA_PAT=${FIGMA_PAT} \
        terraform-orchestra terraform init \
        -backend-config="bucket=orchestra-terraform-state-${ENV}" \
        -backend-config="prefix=terraform/state/${ENV}" \
        "$@"
        
    echo -e "${YELLOW}=== Creating and selecting $ENV workspace ===${NC}"
    docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
        terraform-orchestra terraform workspace new $ENV 2>/dev/null || true
        
    docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
        terraform-orchestra terraform workspace select $ENV
    
    echo -e "${GREEN}Terraform initialized and workspace $ENV selected.${NC}"
    exit 0
elif [ "$TERRAFORM_ACTION" == "workspace" ]; then
    # Handle workspace command directly
    docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
        terraform-orchestra terraform workspace "$@"
    exit 0
fi

# For all other commands, make sure we're in the right workspace
echo -e "${YELLOW}=== Initializing Terraform backend and selecting $ENV workspace ===${NC}"
# Always reconfigure the backend when running apply or other commands after init
echo -e "${YELLOW}=== Initializing Terraform backend and selecting $ENV workspace ===${NC}"
# Pass backend configuration during reinitialization
docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
    -e FIGMA_PAT=${FIGMA_PAT} \
    terraform-orchestra terraform init -reconfigure -auto-approve \
    -backend-config="bucket=orchestra-terraform-state-${ENV}" \
    -backend-config="prefix=terraform/state/${ENV}" \
    "$@"

docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
    terraform-orchestra terraform workspace new $ENV 2>/dev/null || true

docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
    terraform-orchestra terraform workspace select $ENV

# Run the actual Terraform command
echo -e "${YELLOW}=== Running Terraform $TERRAFORM_ACTION for $ENV ===${NC}"

# Determine the correct variable argument
VAR_ARG=""
if [ "$ENV" == "prod" ]; then
    TFVARS_FILE_ABS="/workspace/infra/prod.tfvars" # Use absolute path within container
    VAR_ARG="-var-file=${TFVARS_FILE_ABS}"
else
    VAR_ARG="-var=\"env=$ENV\""
fi

# Execute the Terraform command
docker run $GCLOUD_VOLUME_MOUNT -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
    -e FIGMA_PAT=${FIGMA_PAT} \
    terraform-orchestra terraform $TERRAFORM_ACTION $VAR_ARG "$@"

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Terraform $TERRAFORM_ACTION complete!${NC}"
echo -e "${BLUE}======================================================${NC}"
