#!/bin/bash
# sanitized_migration_script.sh
#
# SANITIZED VERSION: This script replaces sensitive information with placeholders
# for security purposes. Replace placeholders with your actual values before use.

set -e

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - REPLACE WITH YOUR ACTUAL VALUES
GCP_PROJECT_ID="YOUR_PROJECT_ID"        # e.g., "my-project-123"
GCP_ORG_ID="YOUR_ORGANIZATION_ID"       # e.g., "123456789012"
SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT"  # e.g., "service-account@my-project-123.iam.gserviceaccount.com"
KEY_FILE="service-account-key.json"     # Path to your service account key file

echo -e "${BLUE}===== GCP Migration Process - Exact Steps =====${NC}"

# Step 1: Service Account Authentication
echo -e "\n${YELLOW}Step 1: Service Account Authentication${NC}"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
  echo -e "${RED}Error: $KEY_FILE not found.${NC}"
  echo -e "${BLUE}Please create the file with the appropriate service account key content${NC}"
  exit 1
fi

# Set secure permissions on key file
chmod 600 "$KEY_FILE"
echo -e "${GREEN}Key file permissions set to 600 (secure)${NC}"

# Authenticate with service account
echo -e "${BLUE}Authenticating with service account...${NC}"
gcloud auth activate-service-account "$SERVICE_ACCOUNT" --key-file="$KEY_FILE"
echo -e "${GREEN}Authentication successful!${NC}"

# Step 2: Grant Critical Roles
echo -e "\n${YELLOW}Step 2: Grant Critical Roles${NC}"
echo -e "${BLUE}Granting 'resourcemanager.projectMover' role...${NC}"
gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/resourcemanager.projectMover"

echo -e "${BLUE}Granting 'resourcemanager.projectCreator' role...${NC}"
gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/resourcemanager.projectCreator"

# Wait for IAM propagation - CRITICAL
echo -e "${YELLOW}Critical: Waiting 5 minutes for IAM propagation...${NC}"
echo -e "${BLUE}This wait is necessary for the roles to fully propagate...${NC}"
echo -e "Start time: $(date)"

for i in {300..1}; do
  echo -ne "\rWaiting: $i seconds remaining..."
  sleep 1
done
echo -e "\nFinished waiting at: $(date)"
echo -e "${GREEN}IAM propagation period completed${NC}"

# Step 3: Migrate Project
echo -e "\n${YELLOW}Step 3: Migrate Project${NC}"
echo -e "${BLUE}Executing project migration command...${NC}"
gcloud beta projects move "$GCP_PROJECT_ID" \
  --organization="$GCP_ORG_ID" \
  --billing-project="$GCP_PROJECT_ID"

# Step 4: Immediate Verification
echo -e "\n${YELLOW}Step 4: Immediate Verification${NC}"
echo -e "${BLUE}Verifying project organization membership...${NC}"
CURRENT_ORG=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
echo "Current organization ID: $CURRENT_ORG"

if [ "$CURRENT_ORG" = "$GCP_ORG_ID" ]; then
  echo -e "${GREEN}✅ Migration successful! Project is now in organization $GCP_ORG_ID${NC}"
else
  echo -e "${RED}❌ Migration failed! Project is not in the expected organization.${NC}"
  echo -e "${RED}   Current parent: $CURRENT_ORG, Expected: $GCP_ORG_ID${NC}"
  exit 1
fi

# Step 5: Enable Required Services
echo -e "\n${YELLOW}Step 5: Enable Required Services${NC}"
echo -e "${BLUE}Enabling required services...${NC}"
gcloud services enable \
  workstations.googleapis.com \
  aiplatform.googleapis.com \
  redis.googleapis.com \
  alloydb.googleapis.com

# Step 6: Deploy Infrastructure (using Terraform)
echo -e "\n${YELLOW}Step 6: Deploy Infrastructure${NC}"
echo -e "${BLUE}Checking if Terraform is installed...${NC}"
if ! command -v terraform &> /dev/null; then
  echo -e "${RED}Terraform is not installed. Please install it first.${NC}"
  exit 1
fi

# Check if simplified Terraform configuration exists
if [ -f "workstation_config.tf" ]; then
  echo -e "${BLUE}Deploying infrastructure with Terraform...${NC}"
  terraform init
  terraform apply -auto-approve \
    -var="project_id=$GCP_PROJECT_ID" \
    -var="org_id=$GCP_ORG_ID" \
    -var="gpu_type=nvidia-tesla-t4" \
    -var="gpu_count=2"
  echo -e "${GREEN}Infrastructure deployed successfully!${NC}"
else
  echo -e "${YELLOW}Warning: workstation_config.tf not found.${NC}"
  echo -e "${YELLOW}Please create this file with proper workstation configuration.${NC}"
fi

# Step 7: Post-Migration Validation
echo -e "\n${YELLOW}Step 7: Post-Migration Validation${NC}"

echo -e "${BLUE}1. Verifying organization membership...${NC}"
ORG_CHECK=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
echo "Organization ID: $ORG_CHECK $([ "$ORG_CHECK" = "$GCP_ORG_ID" ] && echo "[✔️]" || echo "[❌]")"

echo -e "${BLUE}2. Checking service account roles...${NC}"
ROLES=$(gcloud organizations get-iam-policy "$GCP_ORG_ID" \
  --filter="bindings.members:$SERVICE_ACCOUNT" \
  --format="value(bindings.role)")
echo "Roles assigned to $SERVICE_ACCOUNT:"
echo "$ROLES"

echo -e "${BLUE}3. Checking workstation access...${NC}"
# This will only work if workstations are deployed
WORKSTATIONS=$(gcloud workstations list --project="$GCP_PROJECT_ID" --format="value(name)" 2>/dev/null || echo "No workstations found")
if [[ "$WORKSTATIONS" == *"ai-dev"* ]]; then
  echo -e "${BLUE}Starting workstation for validation...${NC}"
  gcloud workstations start ai-dev-config \
    --cluster=ai-development \
    --region=us-central1
  
  # Get workstation IP
  WORKSTATION_IP=$(gcloud workstations describe ai-dev-config \
    --cluster=ai-development \
    --project="$GCP_PROJECT_ID" \
    --format="value(host)" 2>/dev/null || echo "Unknown")
  echo "Workstation IP: $WORKSTATION_IP [✔️]"
else
  echo -e "${YELLOW}Workstations not found or not fully deployed yet.${NC}"
  echo "Workstation IP: Not available yet [⚠️]"
fi

# Final summary
echo -e "\n${GREEN}===== Migration Process Complete =====${NC}"
echo -e "${BLUE}Your project has been successfully migrated to organization $GCP_ORG_ID${NC}"
echo -e "${BLUE}To access your hybrid IDE, run:${NC}"
echo "gcloud workstations start ai-dev-config --cluster=ai-development --region=us-central1"
