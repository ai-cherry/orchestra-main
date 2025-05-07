#!/bin/bash
# Script to set up remote Terraform state in Google Cloud Storage

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="agi-baby-cherry"
BUCKET_NAME="${PROJECT_ID}-terraform-state"
REGION="us-west2"

echo -e "${GREEN}Setting up remote Terraform state in Google Cloud Storage...${NC}"
echo -e "Project ID: ${YELLOW}${PROJECT_ID}${NC}"
echo -e "Bucket Name: ${YELLOW}${BUCKET_NAME}${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC}"

# Create the GCS bucket
echo -e "${GREEN}Creating GCS bucket for Terraform state...${NC}"
if gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
    echo -e "${YELLOW}Bucket already exists.${NC}"
else
    gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${BUCKET_NAME}"
    echo -e "${GREEN}Bucket created.${NC}"
fi

# Enable versioning on the bucket
echo -e "${GREEN}Enabling versioning on the bucket...${NC}"
gsutil versioning set on "gs://${BUCKET_NAME}"
echo -e "${GREEN}Versioning enabled.${NC}"

# Set lifecycle policy to delete old versions after 30 days
echo -e "${GREEN}Setting lifecycle policy...${NC}"
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "numNewerVersions": 3,
          "age": 30
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json "gs://${BUCKET_NAME}"
rm lifecycle.json
echo -e "${GREEN}Lifecycle policy set.${NC}"

# Update terraform files
echo -e "${GREEN}Updating Terraform backend configuration in dev environment...${NC}"
sed -i.bak 's/# backend "gcs" {/backend "gcs" {/' infra/dev/main.tf
sed -i.bak 's/#   bucket = "agi-baby-cherry-terraform-state"/  bucket = "agi-baby-cherry-terraform-state"/' infra/dev/main.tf
sed -i.bak 's/#   prefix = "orchestra\/dev"/  prefix = "orchestra\/dev"/' infra/dev/main.tf
sed -i.bak 's/# }/}/' infra/dev/main.tf

echo -e "${GREEN}Updating Terraform backend configuration in prod environment...${NC}"
sed -i.bak 's/# backend "gcs" {/backend "gcs" {/' infra/prod/main.tf
sed -i.bak 's/#   bucket = "agi-baby-cherry-terraform-state"/  bucket = "agi-baby-cherry-terraform-state"/' infra/prod/main.tf
sed -i.bak 's/#   prefix = "orchestra\/prod"/  prefix = "orchestra\/prod"/' infra/prod/main.tf
sed -i.bak 's/# }/}/' infra/prod/main.tf

echo -e "${GREEN}Remote state setup complete!${NC}"
echo -e "${GREEN}You can now run 'terraform init -migrate-state' in each environment directory.${NC}"
