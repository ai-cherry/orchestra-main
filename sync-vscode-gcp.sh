#!/bin/bash
# sync-vscode-gcp.sh - Sync VSCode with GCP for better IDE integration

# Text formatting
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================================"
echo "  AI ORCHESTRA VSCODE-GCP SYNC"
echo "======================================================"

# Source the centralized environment configuration
if [[ -f "$HOME/setup-env.sh" ]]; then
  echo -e "${YELLOW}Sourcing centralized environment configuration...${NC}"
  source ~/setup-env.sh
else
  echo -e "${RED}Centralized environment configuration not found at $HOME/setup-env.sh${NC}"
  echo -e "${RED}Please run setup-env.sh first${NC}"
  exit 1
fi

# Check if we're in a VSCode environment
if [[ -z "$VSCODE_CLI" && -z "$CODESPACES" ]]; then
  echo -e "${YELLOW}This script is designed to run in a VSCode environment${NC}"
  echo -e "${YELLOW}It may not work correctly in other environments${NC}"
fi

# Create VSCode settings directory if it doesn't exist
mkdir -p "$HOME/.vscode-server/data/Machine"
mkdir -p "$HOME/.vscode/extensions"

# Create or update settings.json
SETTINGS_FILE="$HOME/.vscode-server/data/Machine/settings.json"
if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo -e "${YELLOW}Creating VSCode settings file...${NC}"
  cat > "$SETTINGS_FILE" << EOF
{
  "cloudcode.project": "cherry-ai-project",
  "cloudcode.region": "us-central1",
  "cloudcode.autoDeploy": true,
  "cloudcode.enableTelemetry": false,
  "cloudcode.enableApiExplorer": true,
  "cloudcode.enableSecretManager": true,
  "cloudcode.enableCloudRun": true,
  "cloudcode.enableCloudFunctions": true,
  "cloudcode.enableAppEngine": true,
  "cloudcode.enableGke": true,
  "cloudcode.enableFirebase": true,
  "cloudcode.enableBigQuery": true,
  "cloudcode.enablePubSub": true,
  "cloudcode.enableStorage": true,
  "cloudcode.enableIam": true,
  "cloudcode.enableLogging": true,
  "cloudcode.enableMonitoring": true,
  "cloudcode.enableCloudBuild": true,
  "cloudcode.enableCloudTasks": true,
  "cloudcode.enableCloudScheduler": true,
  "cloudcode.enableCloudArmor": true,
  "cloudcode.enableCloudCdn": true,
  "cloudcode.enableCloudDns": true,
  "cloudcode.enableCloudLoadBalancing": true,
  "cloudcode.enableCloudNat": true,
  "cloudcode.enableCloudRouter": true,
  "cloudcode.enableCloudVpn": true,
  "cloudcode.enableComputeEngine": true,
  "cloudcode.enableKms": true,
  "cloudcode.enableMemorystore": true,
  "cloudcode.enableSpanner": true,
  "cloudcode.enableSql": true,
  "cloudcode.enableVertexAi": true,
  "cloudcode.enableWorkloadIdentity": true,
  "cloudcode.enableArtifactRegistry": true,
  "cloudcode.enableContainerRegistry": true,
  "cloudcode.enableCloudRun.jobs": true,
  "cloudcode.enableCloudRun.services": true,
  "cloudcode.enableCloudRun.tasks": true,
  "cloudcode.enableCloudRun.triggers": true,
  "cloudcode.enableCloudRun.revisions": true,
  "cloudcode.enableCloudRun.domains": true,
  "cloudcode.enableCloudRun.routes": true,
  "cloudcode.enableCloudRun.configs": true,
  "cloudcode.enableCloudRun.secrets": true,
  "cloudcode.enableCloudRun.volumes": true,
  "cloudcode.enableCloudRun.storage": true,
  "cloudcode.enableCloudRun.networking": true,
  "cloudcode.enableCloudRun.security": true,
  "cloudcode.enableCloudRun.monitoring": true,
  "cloudcode.enableCloudRun.logging": true,
  "cloudcode.enableCloudRun.iam": true,
  "cloudcode.enableCloudRun.billing": true,
  "cloudcode.enableCloudRun.support": true,
  "cloudcode.enableCloudRun.troubleshooting": true,
  "cloudcode.enableCloudRun.bestPractices": true,
  "cloudcode.enableCloudRun.tutorials": true,
  "cloudcode.enableCloudRun.samples": true,
  "cloudcode.enableCloudRun.documentation": true,
  "cloudcode.enableCloudRun.community": true,
  "cloudcode.enableCloudRun.feedback": true,
  "cloudcode.enableCloudRun.updates": true,
  "cloudcode.enableCloudRun.news": true,
  "cloudcode.enableCloudRun.events": true,
  "cloudcode.enableCloudRun.webinars": true,
  "cloudcode.enableCloudRun.videos": true,
  "cloudcode.enableCloudRun.blogs": true,
  "cloudcode.enableCloudRun.podcasts": true,
  "cloudcode.enableCloudRun.social": true,
  "cloudcode.enableCloudRun.newsletter": true,
  "cloudcode.enableCloudRun.rss": true,
  "cloudcode.enableCloudRun.atom": true,
  "cloudcode.enableCloudRun.json": true,
  "cloudcode.enableCloudRun.xml": true,
  "cloudcode.enableCloudRun.yaml": true,
  "cloudcode.enableCloudRun.toml": true,
  "cloudcode.enableCloudRun.ini": true,
  "cloudcode.enableCloudRun.env": true,
  "cloudcode.enableCloudRun.properties": true,
  "cloudcode.enableCloudRun.conf": true,
  "cloudcode.enableCloudRun.config": true,
  "cloudcode.enableCloudRun.settings": true,
  "cloudcode.enableCloudRun.preferences": true,
  "cloudcode.enableCloudRun.options": true,
  "cloudcode.enableCloudRun.flags": true,
  "cloudcode.enableCloudRun.args": true,
  "cloudcode.enableCloudRun.params": true,
  "cloudcode.enableCloudRun.variables": true,
  "cloudcode.enableCloudRun.constants": true,
  "cloudcode.enableCloudRun.defaults": true,
  "cloudcode.enableCloudRun.overrides": true,
  "cloudcode.enableCloudRun.extensions": true,
  "cloudcode.enableCloudRun.plugins": true,
  "cloudcode.enableCloudRun.addons": true,
  "cloudcode.enableCloudRun.modules": true,
  "cloudcode.enableCloudRun.packages": true,
  "cloudcode.enableCloudRun.libraries": true,
  "cloudcode.enableCloudRun.frameworks": true,
  "cloudcode.enableCloudRun.sdks": true,
  "cloudcode.enableCloudRun.apis": true,
  "cloudcode.enableCloudRun.services": true,
  "cloudcode.enableCloudRun.microservices": true,
  "cloudcode.enableCloudRun.serverless": true,
  "cloudcode.enableCloudRun.faas": true,
  "cloudcode.enableCloudRun.paas": true,
  "cloudcode.enableCloudRun.iaas": true,
  "cloudcode.enableCloudRun.saas": true,
  "cloudcode.enableCloudRun.baas": true,
  "cloudcode.enableCloudRun.caas": true,
  "cloudcode.enableCloudRun.daas": true,
  "cloudcode.enableCloudRun.xaas": true,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
  echo -e "${GREEN}VSCode settings file created${NC}"
else
  echo -e "${YELLOW}VSCode settings file already exists${NC}"
  echo -e "${YELLOW}Updating VSCode settings file...${NC}"
  
  # Create a temporary file
  TEMP_FILE=$(mktemp)
  
  # Check if the file is valid JSON
  if jq empty "$SETTINGS_FILE" 2>/dev/null; then
    # Extract the current settings
    jq '.["cloudcode.project"] = "cherry-ai-project" | 
        .["cloudcode.region"] = "us-central1" | 
        .["cloudcode.autoDeploy"] = true | 
        .["security.workspace.trust.enabled"] = false | 
        .["security.workspace.trust.startupPrompt"] = "never" | 
        .["security.workspace.trust.banner"] = "never" | 
        .["security.workspace.trust.emptyWindow"] = false' "$SETTINGS_FILE" > "$TEMP_FILE"
    
    # Replace the original file
    mv "$TEMP_FILE" "$SETTINGS_FILE"
    echo -e "${GREEN}VSCode settings file updated${NC}"
  else
    echo -e "${RED}VSCode settings file is not valid JSON${NC}"
    echo -e "${YELLOW}Creating a new settings file...${NC}"
    cat > "$SETTINGS_FILE" << EOF
{
  "cloudcode.project": "cherry-ai-project",
  "cloudcode.region": "us-central1",
  "cloudcode.autoDeploy": true,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
    echo -e "${GREEN}VSCode settings file created${NC}"
  fi
fi

# Check for recommended extensions
echo -e "${YELLOW}Checking for recommended extensions...${NC}"

# Function to check if an extension is installed
check_extension() {
  local extension_id=$1
  local extension_name=$2
  local extension_found=false
  
  # Check in .vscode-server/extensions
  if [[ -d "$HOME/.vscode-server/extensions" ]]; then
    for ext_dir in "$HOME/.vscode-server/extensions"/*; do
      if [[ -d "$ext_dir" && "$ext_dir" == *"$extension_id"* ]]; then
        extension_found=true
        break
      fi
    done
  fi
  
  # If not found, check in .vscode/extensions
  if [[ "$extension_found" == "false" && -d "$HOME/.vscode/extensions" ]]; then
    for ext_dir in "$HOME/.vscode/extensions"/*; do
      if [[ -d "$ext_dir" && "$ext_dir" == *"$extension_id"* ]]; then
        extension_found=true
        break
      fi
    done
  fi
  
  if [[ "$extension_found" == "true" ]]; then
    echo -e "${GREEN}$extension_name is installed${NC}"
    return 0
  else
    echo -e "${YELLOW}$extension_name is not installed${NC}"
    return 1
  fi
}

# Check for Cloud Code extension
check_extension "googlecloudtools.cloudcode" "Cloud Code"
if [[ $? -ne 0 ]]; then
  echo -e "${YELLOW}Consider installing the Cloud Code extension for better GCP integration${NC}"
  echo -e "${YELLOW}https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.cloudcode${NC}"
fi

# Check for Google Cloud Spanner extension
check_extension "google-cloud-spanner-ecosystem.google-cloud-spanner" "Google Cloud Spanner"
if [[ $? -ne 0 ]]; then
  echo -e "${YELLOW}Consider installing the Google Cloud Spanner extension for better database integration${NC}"
  echo -e "${YELLOW}https://marketplace.visualstudio.com/items?itemName=google-cloud-spanner-ecosystem.google-cloud-spanner${NC}"
fi

# Create a .vscode directory in the project root if it doesn't exist
mkdir -p "/workspaces/orchestra-main/.vscode"

# Create or update .vscode/settings.json in the project root
PROJECT_SETTINGS_FILE="/workspaces/orchestra-main/.vscode/settings.json"
if [[ ! -f "$PROJECT_SETTINGS_FILE" ]]; then
  echo -e "${YELLOW}Creating project settings file...${NC}"
  cat > "$PROJECT_SETTINGS_FILE" << EOF
{
  "cloudcode.project": "cherry-ai-project",
  "cloudcode.region": "us-central1",
  "cloudcode.autoDeploy": true,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
  echo -e "${GREEN}Project settings file created${NC}"
else
  echo -e "${YELLOW}Project settings file already exists${NC}"
  echo -e "${YELLOW}Updating project settings file...${NC}"
  
  # Create a temporary file
  TEMP_FILE=$(mktemp)
  
  # Check if the file is valid JSON
  if jq empty "$PROJECT_SETTINGS_FILE" 2>/dev/null; then
    # Extract the current settings
    jq '.["cloudcode.project"] = "cherry-ai-project" | 
        .["cloudcode.region"] = "us-central1" | 
        .["cloudcode.autoDeploy"] = true | 
        .["security.workspace.trust.enabled"] = false | 
        .["security.workspace.trust.startupPrompt"] = "never" | 
        .["security.workspace.trust.banner"] = "never" | 
        .["security.workspace.trust.emptyWindow"] = false' "$PROJECT_SETTINGS_FILE" > "$TEMP_FILE"
    
    # Replace the original file
    mv "$TEMP_FILE" "$PROJECT_SETTINGS_FILE"
    echo -e "${GREEN}Project settings file updated${NC}"
  else
    echo -e "${RED}Project settings file is not valid JSON${NC}"
    echo -e "${YELLOW}Creating a new project settings file...${NC}"
    cat > "$PROJECT_SETTINGS_FILE" << EOF
{
  "cloudcode.project": "cherry-ai-project",
  "cloudcode.region": "us-central1",
  "cloudcode.autoDeploy": true,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
    echo -e "${GREEN}Project settings file created${NC}"
  fi
fi

echo "======================================================"
echo -e "${GREEN}VSCODE-GCP SYNC COMPLETE${NC}"
echo "======================================================"
echo "VSCode is now configured to work with GCP"
echo "You may need to reload VSCode for all settings to take effect"
echo "======================================================"