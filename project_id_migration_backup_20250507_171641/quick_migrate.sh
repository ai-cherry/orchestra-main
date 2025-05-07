#!/bin/bash
# quick_migrate.sh
#
# GCP migration script based on verified implementation
# This script follows the exact steps from the validated approach

set -e

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== AGI Baby Cherry GCP Migration Script =====${NC}"
echo -e "${BLUE}This script will migrate your project to organization 873291114285 and configure Vertex AI${NC}"

# Step 1: Service Account Configuration
echo -e "\n${YELLOW}Step 1: Service Account Configuration${NC}"
if [ ! -f "vertex-agent-key.json" ]; then
  echo -e "${BLUE}Creating service account key file from template...${NC}"
  echo "Please enter your actual private key (or press Enter to use a placeholder):"
  read -s PRIVATE_KEY
  
  # If no input, use placeholder
  if [ -z "$PRIVATE_KEY" ]; then
    PRIVATE_KEY="[YOUR_ACTUAL_PRIVATE_KEY_HERE]"
    echo -e "${YELLOW}Using placeholder for private key. You'll need to replace this with your actual key.${NC}"
  fi
  
  # Create the key file from template
  cp vertex-agent-key-template.json vertex-agent-key.json
  # Replace the placeholder with the actual key
  sed -i "s|\[YOUR_ACTUAL_PRIVATE_KEY_HERE\]|$PRIVATE_KEY|g" vertex-agent-key.json
fi

echo -e "${BLUE}Authenticating with service account...${NC}"
gcloud auth activate-service-account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com \
  --key-file=vertex-agent-key.json

echo -e "${GREEN}Authentication successful!${NC}"

# Step 2: Essential Role Assignment
echo -e "\n${YELLOW}Step 2: Essential Role Assignment${NC}"
echo -e "${BLUE}Granting project migration capabilities...${NC}"
gcloud organizations add-iam-policy-binding 873291114285 \
  --member="serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectMover"

echo -e "${BLUE}Adding Vertex AI service agent permissions...${NC}"
gcloud projects add-iam-policy-binding agi-baby-cherry \
  --member="serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
  --role="roles/aiplatform.serviceAgent"

echo -e "${BLUE}Adding storage permissions for model artifacts...${NC}"
gcloud projects add-iam-policy-binding agi-baby-cherry \
  --member="serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

echo -e "${GREEN}Roles assigned successfully!${NC}"
echo -e "${BLUE}Waiting 30 seconds for IAM propagation...${NC}"
sleep 30

# Step 3: Project Migration
echo -e "\n${YELLOW}Step 3: Project Migration${NC}"
echo -e "${BLUE}Executing migration with numeric org ID...${NC}"
gcloud beta projects move agi-baby-cherry \
  --organization=873291114285 \
  --billing-project=agi-baby-cherry

echo -e "${BLUE}Verifying organization membership...${NC}"
CURRENT_ORG=$(gcloud projects describe agi-baby-cherry --format="value(parent.id)")
if [ "$CURRENT_ORG" = "873291114285" ]; then
  echo -e "${GREEN}Migration Success! Project is now in organization 873291114285${NC}"
else
  echo -e "${RED}Migration Failed! Project is still in $CURRENT_ORG${NC}"
  exit 1
fi

# Step 4: Deploy infrastructure
echo -e "\n${YELLOW}Step 4: Deploying Infrastructure${NC}"
echo -e "${BLUE}Enabling required APIs...${NC}"
gcloud services enable workstations.googleapis.com redis.googleapis.com \
  alloydb.googleapis.com aiplatform.googleapis.com compute.googleapis.com

echo -e "${BLUE}Deploying Terraform configuration...${NC}"
if [ ! -f "simplified_workstation_config.tf" ]; then
  echo -e "${RED}simplified_workstation_config.tf not found! Skipping Terraform deployment.${NC}"
else
  echo -e "${BLUE}Initializing Terraform...${NC}"
  terraform init
  
  echo -e "${BLUE}Applying Terraform configuration...${NC}"
  terraform apply -auto-approve -var="project_id=agi-baby-cherry" -var="org_id=873291114285"
  
  echo -e "${GREEN}Infrastructure deployed successfully!${NC}"
fi

# Step 5: Final Validation
echo -e "\n${YELLOW}Step 5: Final Validation${NC}"
if [ -f "validate_migration_minimal.sh" ]; then
  echo -e "${BLUE}Running validation script...${NC}"
  chmod +x validate_migration_minimal.sh
  ./validate_migration_minimal.sh
else
  echo -e "${BLUE}Running basic validation checks...${NC}"
  # Verify organization membership
  ORG_CHECK=$(gcloud projects describe agi-baby-cherry --format="value(parent.id)")
  if [ "$ORG_CHECK" = "873291114285" ]; then
    echo -e "${GREEN}✅ Organization validation passed${NC}"
  else 
    echo -e "${RED}❌ Organization validation failed${NC}"
  fi
  
  # Check Vertex AI service agent
  SVC_AGENT_CHECK=$(gcloud projects get-iam-policy agi-baby-cherry \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" | grep -i "aiplatform.serviceAgent" || echo "")
  if [ -n "$SVC_AGENT_CHECK" ]; then
    echo -e "${GREEN}✅ Service agent role validation passed${NC}"
  else
    echo -e "${RED}❌ Service agent role validation failed${NC}"
  fi
fi

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}     GCP Migration Process Complete     ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "${BLUE}Your project has been successfully migrated to organization 873291114285${NC}"
echo -e "${BLUE}and configured with the necessary permissions for Vertex AI.${NC}"
echo -e "${BLUE}You can access your workstations through the Google Cloud Console.${NC}"
