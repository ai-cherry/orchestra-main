#!/bin/bash
# validate_migration_and_claude.sh
#
# Comprehensive validation script for GCP migration and Claude Code setup
# Verifies project organization, workstation deployment, and Claude Code installation

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GCP_PROJECT_ID="cherry-ai-project"
GCP_ORG_ID="873291114285"
CLOUD_WORKSTATION_CLUSTER="ai-development"
CLOUD_WORKSTATION_CONFIG="ai-dev-config"
REGION="us-west4"

echo -e "${BLUE}===== GCP Migration and Claude Code Validation =====${NC}"

# -----[ GCP Migration Validation ]-----
echo -e "\n${YELLOW}1. GCP Project Migration Validation${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK (gcloud) is not installed${NC}"
    echo -e "   Please install it first or run execute_gcp_migration.sh"
    exit 1
else
    echo -e "${GREEN}✅ Google Cloud SDK is installed${NC}"
    GCLOUD_VERSION=$(gcloud --version | head -n 1)
    echo -e "   Version: $GCLOUD_VERSION"
fi

# Check current project
echo -e "\n${BLUE}Checking current project...${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "Not set")
echo -e "Current project: $CURRENT_PROJECT"

if [ "$CURRENT_PROJECT" != "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️ Current project is not $GCP_PROJECT_ID${NC}"
    echo -e "${BLUE}Setting project to $GCP_PROJECT_ID...${NC}"
    gcloud config set project "$GCP_PROJECT_ID"
fi

# Check organization membership
echo -e "\n${BLUE}Checking organization membership...${NC}"
ORG_CHECK=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "Failed to retrieve")

if [ "$ORG_CHECK" == "$GCP_ORG_ID" ]; then
    echo -e "${GREEN}✅ Project is in the correct organization: $GCP_ORG_ID${NC}"
else
    echo -e "${RED}❌ Project is NOT in the correct organization${NC}"
    echo -e "   Current organization: $ORG_CHECK"
    echo -e "   Expected organization: $GCP_ORG_ID"
    echo -e "   Run execute_gcp_migration.sh to perform the migration"
fi

# Check billing
echo -e "\n${BLUE}Checking billing account...${NC}"
BILLING_ACCOUNT=$(gcloud billing projects describe "$GCP_PROJECT_ID" --format="value(billingAccountName)" 2>/dev/null || echo "No billing account")

if [ "$BILLING_ACCOUNT" == "No billing account" ]; then
    echo -e "${RED}❌ No billing account attached to the project${NC}"
    echo -e "   Run execute_gcp_migration.sh or link a billing account manually"
else
    echo -e "${GREEN}✅ Project has billing enabled${NC}"
    echo -e "   Billing account: $BILLING_ACCOUNT"
fi

# Check required APIs
echo -e "\n${BLUE}Checking required APIs...${NC}"
REQUIRED_APIS=("workstations.googleapis.com" "aiplatform.googleapis.com" "redis.googleapis.com" "alloydb.googleapis.com")
ALL_APIS_ENABLED=true

for api in "${REQUIRED_APIS[@]}"; do
    API_STATUS=$(gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>/dev/null || echo "")
    
    if [ -z "$API_STATUS" ]; then
        echo -e "${RED}❌ $api is NOT enabled${NC}"
        ALL_APIS_ENABLED=false
    else
        echo -e "${GREEN}✅ $api is enabled${NC}"
    fi
done

if [ "$ALL_APIS_ENABLED" = false ]; then
    echo -e "\n${YELLOW}⚠️ Some required APIs are not enabled. Run execute_gcp_migration.sh to enable them.${NC}"
fi

# Check Cloud Workstation
echo -e "\n${BLUE}Checking Cloud Workstation...${NC}"
WORKSTATION_CLUSTER=$(gcloud workstations clusters list --format="value(name)" 2>/dev/null | grep -i "$CLOUD_WORKSTATION_CLUSTER" || echo "")

if [ -z "$WORKSTATION_CLUSTER" ]; then
    echo -e "${RED}❌ Cloud Workstation cluster '$CLOUD_WORKSTATION_CLUSTER' not found${NC}"
    echo -e "   Run execute_gcp_migration.sh to deploy the workstation"
else
    echo -e "${GREEN}✅ Cloud Workstation cluster exists${NC}"
    
    # Check workstation configuration
    WORKSTATION_CONFIG=$(gcloud workstations configs list --cluster="$CLOUD_WORKSTATION_CLUSTER" --format="value(name)" 2>/dev/null | grep -i "$CLOUD_WORKSTATION_CONFIG" || echo "")
    
    if [ -z "$WORKSTATION_CONFIG" ]; then
        echo -e "${RED}❌ Workstation configuration '$CLOUD_WORKSTATION_CONFIG' not found${NC}"
    else
        echo -e "${GREEN}✅ Workstation configuration exists${NC}"
        
        # Check GPU configuration
        echo -e "${BLUE}Checking GPU configuration...${NC}"
        GPU_CONFIG=$(gcloud workstations configs describe "$CLOUD_WORKSTATION_CONFIG" --cluster="$CLOUD_WORKSTATION_CLUSTER" --location="$REGION" --format="json" 2>/dev/null | grep -A 3 "accelerator" || echo "No GPU")
        
        if [[ "$GPU_CONFIG" == *"nvidia-tesla-t4"* && "$GPU_CONFIG" == *"count\": 2"* ]]; then
            echo -e "${GREEN}✅ Workstation has 2x NVIDIA Tesla T4 GPUs${NC}"
        else
            echo -e "${YELLOW}⚠️ Workstation does not have the expected GPU configuration${NC}"
            echo -e "   Current configuration: $GPU_CONFIG"
            echo -e "   Expected: 2x NVIDIA Tesla T4"
        fi
        
        # Check machine type
        MACHINE_TYPE=$(gcloud workstations configs describe "$CLOUD_WORKSTATION_CONFIG" --cluster="$CLOUD_WORKSTATION_CLUSTER" --location="$REGION" --format="value(host.gceInstance.machineType)" 2>/dev/null || echo "Unknown")
        
        if [ "$MACHINE_TYPE" == "n2d-standard-32" ]; then
            echo -e "${GREEN}✅ Workstation has the correct machine type: n2d-standard-32${NC}"
        else
            echo -e "${YELLOW}⚠️ Workstation does not have the expected machine type${NC}"
            echo -e "   Current machine type: $MACHINE_TYPE"
            echo -e "   Expected: n2d-standard-32"
        fi
    fi
fi

# -----[ Claude Code Validation ]-----
echo -e "\n${YELLOW}2. Claude Code Validation${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo -e "   Run setup_claude_code.sh to install Node.js"
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✅ Node.js is installed: $NODE_VERSION${NC}"
fi

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo -e "${RED}❌ Claude Code is not installed${NC}"
    echo -e "   Run setup_claude_code.sh to install Claude Code"
else
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "Unknown")
    echo -e "${GREEN}✅ Claude Code is installed: $CLAUDE_VERSION${NC}"
fi

# Check if CLAUDE.md exists
if [ -f "CLAUDE.md" ]; then
    echo -e "${GREEN}✅ CLAUDE.md project memory file exists${NC}"
else
    echo -e "${YELLOW}⚠️ CLAUDE.md project memory file does not exist${NC}"
    echo -e "   Run setup_claude_code.sh to create the project memory file"
fi

# Check Claude Code configuration
if [ -f "$HOME/.claude/config.json" ]; then
    echo -e "${GREEN}✅ Claude Code configuration exists${NC}"
else
    echo -e "${YELLOW}⚠️ Claude Code configuration does not exist${NC}"
    echo -e "   Run setup_claude_code.sh to create the configuration file"
fi

# -----[ Final Summary ]-----
echo -e "\n${YELLOW}Summary${NC}"

echo -e "${BLUE}GCP Migration:${NC}"
if [ "$ORG_CHECK" == "$GCP_ORG_ID" ] && [ "$BILLING_ACCOUNT" != "No billing account" ] && [ "$ALL_APIS_ENABLED" = true ] && [ ! -z "$WORKSTATION_CLUSTER" ]; then
    echo -e "${GREEN}✅ GCP Migration is complete and verified${NC}"
else
    echo -e "${YELLOW}⚠️ GCP Migration is incomplete or has issues${NC}"
    echo -e "   Run execute_gcp_migration.sh to complete the migration"
fi

echo -e "${BLUE}Claude Code Setup:${NC}"
if command -v node &> /dev/null && command -v claude &> /dev/null && [ -f "CLAUDE.md" ]; then
    echo -e "${GREEN}✅ Claude Code is set up and ready to use${NC}"
else
    echo -e "${YELLOW}⚠️ Claude Code setup is incomplete${NC}"
    echo -e "   Run setup_claude_code.sh to complete the setup"
fi

echo -e "\n${GREEN}===== Validation Complete =====${NC}"
echo -e "${BLUE}For detailed information, see README-CLAUDE-GCP-MIGRATION.md${NC}"
