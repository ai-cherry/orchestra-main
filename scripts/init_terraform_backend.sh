#!/bin/bash
# Initialize Terraform Backend on GCP
# This script creates a GCS bucket for Terraform state storage and enables required APIs

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
BUCKET_NAME="${PROJECT_ID}-terraform-state"
BUCKET_LOCATION="us-west4"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Initializing Terraform backend on GCP...${NC}"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable storage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project ${PROJECT_ID}

# Create GCS bucket for Terraform state if it doesn't exist
echo -e "${YELLOW}Checking if Terraform state bucket exists...${NC}"
if gsutil ls -p ${PROJECT_ID} gs://${BUCKET_NAME} &>/dev/null; then
    echo -e "${YELLOW}Bucket ${BUCKET_NAME} already exists. Skipping creation.${NC}"
else
    echo -e "${YELLOW}Creating GCS bucket for Terraform state...${NC}"
    gsutil mb -p ${PROJECT_ID} -l ${BUCKET_LOCATION} gs://${BUCKET_NAME}
    echo -e "${GREEN}Bucket created successfully.${NC}"
    
    # Enable versioning on the bucket
    echo -e "${YELLOW}Enabling versioning on the bucket...${NC}"
    gsutil versioning set on gs://${BUCKET_NAME}
    
    # Set lifecycle policy to delete old versions after 30 days
    echo -e "${YELLOW}Setting lifecycle policy...${NC}"
    cat > /tmp/lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "numNewerVersions": 3,
        "age": 30
      }
    }
  ]
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json gs://${BUCKET_NAME}
    rm /tmp/lifecycle.json
fi

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
cd /workspaces/orchestra-main/terraform
terraform init -reconfigure \
    -backend-config="bucket=${BUCKET_NAME}" \
    -backend-config="prefix=terraform/state"

echo -e "${GREEN}Terraform backend initialized successfully!${NC}"
echo -e "${YELLOW}You can now run 'terraform plan' and 'terraform apply' to manage your infrastructure.${NC}"