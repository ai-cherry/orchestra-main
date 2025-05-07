#!/bin/bash

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  COMPREHENSIVE GCP CODESPACE SETUP VERIFICATION${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Check if gcloud is in PATH
echo -e "\n${BLUE}Checking gcloud installation:${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud not found in PATH. Attempting to fix...${NC}"
    export PATH=$PATH:/home/vscode/google-cloud-sdk/bin:/workspaces/orchestra-main/google-cloud-sdk/bin
    echo 'export PATH=$PATH:/home/vscode/google-cloud-sdk/bin:/workspaces/orchestra-main/google-cloud-sdk/bin' >> $HOME/.bashrc
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud still not found. Manual installation may be required:${NC}"
        echo -e "${YELLOW}Run these commands:${NC}"
        echo -e "  curl https://sdk.cloud.google.com | bash"
        echo -e "  exec -l \$SHELL"
        echo -e "  gcloud init"
    fi
else
    echo -e "${GREEN}✅ gcloud is installed and in PATH${NC}"
    echo -e "${BLUE}gcloud location: $(which gcloud)${NC}"
    echo -e "${BLUE}gcloud version: $(gcloud --version | head -1)${NC}"
fi

# Check service account key file
echo -e "\n${BLUE}Checking service account key file:${NC}"
if [ ! -f "$HOME/.gcp/service-account.json" ]; then
    echo -e "${RED}❌ Service account key file not found at $HOME/.gcp/service-account.json${NC}"
    echo -e "${YELLOW}Creating directory and attempting to create key file from environment variable...${NC}"
    
    mkdir -p $HOME/.gcp
    
    if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
        echo $GCP_MASTER_SERVICE_JSON > $HOME/.gcp/service-account.json
        echo -e "${GREEN}✅ Created service account key file from GCP_MASTER_SERVICE_JSON${NC}"
    else
        echo -e "${RED}❌ GCP_MASTER_SERVICE_JSON environment variable not set${NC}"
        echo -e "${YELLOW}Please set GCP_MASTER_SERVICE_JSON with your service account key JSON${NC}"
    fi
else
    echo -e "${GREEN}✅ Service account key file exists at $HOME/.gcp/service-account.json${NC}"
    
    # Verify it's valid JSON
    if jq . $HOME/.gcp/service-account.json >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Service account key file contains valid JSON${NC}"
    else
        echo -e "${RED}❌ Service account key file does not contain valid JSON${NC}"
    fi
fi

# Verify authentication
echo -e "\n${BLUE}Checking authentication:${NC}"
ACTIVE_ACCOUNT=$(gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>/dev/null)
if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo -e "${RED}❌ No active gcloud account found${NC}"
    
    if [ -f "$HOME/.gcp/service-account.json" ]; then
        echo -e "${YELLOW}Attempting to authenticate with service account key...${NC}"
        gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json
    fi
elif [ "$ACTIVE_ACCOUNT" != "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com" ]; then
    echo -e "${YELLOW}⚠️ Active account ($ACTIVE_ACCOUNT) is not the expected service account${NC}"
    echo -e "${YELLOW}Attempting to authenticate with the correct service account...${NC}"
    
    if [ -f "$HOME/.gcp/service-account.json" ]; then
        gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=$HOME/.gcp/service-account.json
    fi
else
    echo -e "${GREEN}✅ Authentication: $ACTIVE_ACCOUNT${NC}"
fi

# Verify project
echo -e "\n${BLUE}Checking project:${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ]; then
    echo -e "${RED}❌ No project set${NC}"
    echo -e "${YELLOW}Setting project to cherry-ai-project...${NC}"
    gcloud config set project cherry-ai-project
elif [ "$CURRENT_PROJECT" != "cherry-ai-project" ]; then
    echo -e "${YELLOW}⚠️ Project is set to $CURRENT_PROJECT, not cherry-ai-project${NC}"
    echo -e "${YELLOW}Setting project to cherry-ai-project...${NC}"
    gcloud config set project cherry-ai-project
else
    echo -e "${GREEN}✅ Project: $CURRENT_PROJECT${NC}"
fi

# Verify credentials environment variable
echo -e "\n${BLUE}Checking credentials environment variable:${NC}"
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${RED}❌ GOOGLE_APPLICATION_CREDENTIALS is not set${NC}"
    echo -e "${YELLOW}Setting GOOGLE_APPLICATION_CREDENTIALS to $HOME/.gcp/service-account.json...${NC}"
    export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
elif [ "$GOOGLE_APPLICATION_CREDENTIALS" != "$HOME/.gcp/service-account.json" ]; then
    echo -e "${YELLOW}⚠️ GOOGLE_APPLICATION_CREDENTIALS is set to $GOOGLE_APPLICATION_CREDENTIALS, not $HOME/.gcp/service-account.json${NC}"
    echo -e "${YELLOW}Updating GOOGLE_APPLICATION_CREDENTIALS...${NC}"
    export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
else
    echo -e "${GREEN}✅ Credentials path: $GOOGLE_APPLICATION_CREDENTIALS${NC}"
fi

# Check for recovery container
echo -e "\n${BLUE}Checking for recovery container:${NC}"
if grep -q "recovery container" ../.codespaces/.persistedshare/creation.log 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Codespace was created using a recovery container${NC}"
    echo -e "${YELLOW}⚠️ This indicates that your original container configuration failed to build${NC}"
    echo -e "${YELLOW}⚠️ The GCP feature may not have been installed properly${NC}"
    
    if grep -q "Feature.*gcloud.*could not be processed" ../.codespaces/.persistedshare/creation.log 2>/dev/null; then
        echo -e "${RED}❌ Found error with GCP feature installation in creation log${NC}"
        echo -e "${YELLOW}⚠️ This may require manually installing gcloud SDK${NC}"
    fi
else
    echo -e "${GREEN}✅ Codespace created with proper container configuration${NC}"
fi

# Check for restricted mode
echo -e "\n${BLUE}Checking workspace trust/restricted mode settings:${NC}"
if [ "$VSCODE_DISABLE_WORKSPACE_TRUST" = "true" ]; then
    echo -e "${GREEN}✅ VSCODE_DISABLE_WORKSPACE_TRUST is set to true${NC}"
else
    echo -e "${RED}❌ VSCODE_DISABLE_WORKSPACE_TRUST is not set to true${NC}"
    echo -e "${YELLOW}⚠️ Restricted mode may be active, which could affect GCP authentication${NC}"
fi

# Test GCP functionality
echo -e "\n${BLUE}Testing basic GCP functionality:${NC}"
echo -e "${YELLOW}Attempting to list GCP projects...${NC}"
if gcloud projects list --limit=1 &>/dev/null; then
    echo -e "${GREEN}✅ Successfully connected to GCP and listed projects${NC}"
else
    echo -e "${RED}❌ Failed to list GCP projects${NC}"
    echo -e "${YELLOW}⚠️ GCP authentication may not be properly configured${NC}"
fi

echo -e "\n${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${GREEN}  GCP VERIFICATION COMPLETE${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

echo -e "\n${YELLOW}If GCP authentication is still not working:${NC}"
echo -e "${BLUE}1. Try manually installing and configuring gcloud:${NC}"
echo -e "   curl https://sdk.cloud.google.com | bash"
echo -e "   exec -l \$SHELL"
echo -e "   mkdir -p \$HOME/.gcp"
echo -e "   echo \$GCP_MASTER_SERVICE_JSON > \$HOME/.gcp/service-account.json"
echo -e "   gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=\$HOME/.gcp/service-account.json"
echo -e "   gcloud config set project cherry-ai-project"
echo -e "${BLUE}2. Ensure standard mode is enabled using verify_standard_mode.sh${NC}"
echo -e "${BLUE}3. If issues persist, rebuild the Codespace or contact GitHub support${NC}"
