#!/bin/bash
# update_codespaces_secrets.sh - Update GitHub Codespaces secrets and configuration
# This script updates GitHub Codespaces with the necessary secrets and configuration for GCP integration

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${GITHUB_REPO:=orchestra-main}"
: "${REGION:=us-central1}"

# Log function with timestamps
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${GREEN}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "INFO" "Checking requirements..."
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    log "ERROR" "GitHub CLI (gh) is required but not found"
    log "INFO" "Please install it: https://cli.github.com/manual/installation"
    exit 1
  fi
  
  # Check for GitHub PAT
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    exit 1
  fi
  
  # Check for GCP_VERTEX_POWER_KEY
  if [[ -z "${GCP_VERTEX_POWER_KEY}" ]]; then
    log "ERROR" "GCP_VERTEX_POWER_KEY environment variable is required"
    exit 1
  fi
  
  # Check for GCP_GEMINI_POWER_KEY
  if [[ -z "${GCP_GEMINI_POWER_KEY}" ]]; then
    log "ERROR" "GCP_GEMINI_POWER_KEY environment variable is required"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GitHub
authenticate_github() {
  log "INFO" "Authenticating with GitHub using GITHUB_TOKEN..."
  echo "${GITHUB_TOKEN}" | gh auth login --with-token
  
  # Verify GitHub authentication
  if ! gh auth status &>/dev/null; then
    log "ERROR" "Failed to authenticate with GitHub"
    exit 1
  fi
  
  log "INFO" "Successfully authenticated with GitHub"
}

# Update GitHub Codespaces secrets
update_codespaces_secrets() {
  log "INFO" "Updating GitHub Codespaces secrets..."
  
  # Set the GCP_VERTEX_POWER_KEY secret for Codespaces
  log "INFO" "Setting GCP_VERTEX_POWER_KEY secret for Codespaces"
  echo "${GCP_VERTEX_POWER_KEY}" | gh secret set "GCP_VERTEX_POWER_KEY" --repo "${GITHUB_ORG}/${GITHUB_REPO}" --body -
  
  # Set the GCP_GEMINI_POWER_KEY secret for Codespaces
  log "INFO" "Setting GCP_GEMINI_POWER_KEY secret for Codespaces"
  echo "${GCP_GEMINI_POWER_KEY}" | gh secret set "GCP_GEMINI_POWER_KEY" --repo "${GITHUB_ORG}/${GITHUB_REPO}" --body -
  
  # Set the GCP_PROJECT_ID secret for Codespaces
  log "INFO" "Setting GCP_PROJECT_ID secret for Codespaces to: ${GCP_PROJECT_ID}"
  gh secret set "GCP_PROJECT_ID" --repo "${GITHUB_ORG}/${GITHUB_REPO}" --body "${GCP_PROJECT_ID}"
  
  # Set the GCP_REGION secret for Codespaces
  log "INFO" "Setting GCP_REGION secret for Codespaces to: ${REGION}"
  gh secret set "GCP_REGION" --repo "${GITHUB_ORG}/${GITHUB_REPO}" --body "${REGION}"
  
  log "INFO" "GitHub Codespaces secrets updated successfully"
}

# Create or update Codespaces devcontainer.json configuration
update_devcontainer_config() {
  log "INFO" "Updating Codespaces devcontainer.json configuration..."
  
  local devcontainer_dir=".devcontainer"
  local devcontainer_file="${devcontainer_dir}/devcontainer.json"
  
  # Create .devcontainer directory if it doesn't exist
  if [ ! -d "${devcontainer_dir}" ]; then
    log "INFO" "Creating ${devcontainer_dir} directory"
    mkdir -p "${devcontainer_dir}"
  fi
  
  # Check if devcontainer.json exists
  if [ -f "${devcontainer_file}" ]; then
    log "INFO" "Backing up existing ${devcontainer_file}"
    cp "${devcontainer_file}" "${devcontainer_file}.backup"
  fi
  
  # Create or update devcontainer.json
  log "INFO" "Creating ${devcontainer_file}"
  cat > "${devcontainer_file}" << EOF
{
  "name": "AI Orchestra Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/terraform:1": {},
    "ghcr.io/devcontainers/features/gcloud:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-azuretools.vscode-docker",
        "hashicorp.terraform",
        "googlecloudtools.cloudcode",
        "googlecloudtools.cloudcode-gemini"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": true,
        "python.formatting.provider": "black",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.organizeImports": true
        },
        "geminiCodeAssist.projectId": "${GCP_PROJECT_ID}",
        "geminiCodeAssist.contextAware": true,
        "geminiCodeAssist.codeReview.enabled": true,
        "cloudcode.duetAI.project": "${GCP_PROJECT_ID}"
      }
    }
  },
  "postCreateCommand": "bash -c 'scripts/setup_codespaces_env.sh'",
  "remoteEnv": {
    "GCP_PROJECT_ID": "${GCP_PROJECT_ID}",
    "GCP_REGION": "${REGION}"
  }
}
EOF
  
  log "INFO" "Codespaces devcontainer.json configuration updated successfully"
}

# Create or update Codespaces setup script
create_codespaces_setup_script() {
  log "INFO" "Creating Codespaces setup script..."
  
  local setup_script="scripts/setup_codespaces_env.sh"
  
  # Create or update setup script
  log "INFO" "Creating ${setup_script}"
  cat > "${setup_script}" << 'EOFMARKER'
#!/bin/bash
# setup_codespaces_env.sh - Set up Codespaces environment for AI Orchestra

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Codespaces environment for AI Orchestra...${NC}"

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install poetry
poetry install

# Set up gcloud CLI
echo -e "${BLUE}Setting up gcloud CLI...${NC}"
if [ -n "$GCP_VERTEX_POWER_KEY" ]; then
  echo -e "${GREEN}GCP_VERTEX_POWER_KEY found, setting up authentication...${NC}"
  echo "$GCP_VERTEX_POWER_KEY" > /tmp/vertex-key.json
  gcloud auth activate-service-account --key-file=/tmp/vertex-key.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-key.json
  echo "export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-key.json" >> ~/.bashrc
  
  # Set default project and region
  if [ -n "$GCP_PROJECT_ID" ]; then
    gcloud config set project "$GCP_PROJECT_ID"
  fi
  
  if [ -n "$GCP_REGION" ]; then
    gcloud config set compute/region "$GCP_REGION"
  fi
else
  echo -e "${YELLOW}GCP_VERTEX_POWER_KEY not found, skipping gcloud authentication${NC}"
  echo -e "${YELLOW}You will need to authenticate manually with 'gcloud auth login'${NC}"
fi

# Set up Gemini Code Assist
echo -e "${BLUE}Setting up Gemini Code Assist...${NC}"
if [ -n "$GCP_GEMINI_POWER_KEY" ]; then
  echo -e "${GREEN}GCP_GEMINI_POWER_KEY found, setting up Gemini configuration...${NC}"
  mkdir -p ~/.config/google-cloud-tools
  cat > ~/.config/google-cloud-tools/.gemini-code-assist.yaml << INNEREOF
project_id: \${GCP_PROJECT_ID:-cherry-ai-project}
location: \${GCP_REGION:-us-central1}
INNEREOF
else
  echo -e "${YELLOW}GCP_GEMINI_POWER_KEY not found, skipping Gemini configuration${NC}"
fi

# Install pre-commit hooks
echo -e "${BLUE}Setting up pre-commit hooks...${NC}"
if [ -f ".git/hooks/pre-commit" ]; then
  echo -e "${YELLOW}Pre-commit hook already exists, skipping${NC}"
else
  if [ -f "scripts/install-pre-commit-hook.sh" ]; then
    bash scripts/install-pre-commit-hook.sh
  else
    echo -e "${YELLOW}Pre-commit hook installation script not found, skipping${NC}"
  fi
fi

echo -e "${GREEN}Codespaces environment setup complete!${NC}"
echo -e "${BLUE}You can now start developing with AI Orchestra.${NC}"
EOFMARKER
  
  # Make the script executable
  chmod +x "${setup_script}"
  
  log "INFO" "Codespaces setup script created successfully"
}

# Main function
main() {
  log "INFO" "Starting GitHub Codespaces configuration update..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Update GitHub Codespaces secrets
  update_codespaces_secrets
  
  # Update devcontainer.json configuration
  update_devcontainer_config
  
  # Create Codespaces setup script
  create_codespaces_setup_script
  
  log "INFO" "GitHub Codespaces configuration update complete!"
  log "INFO" "Next steps:"
  log "INFO" "1. Commit and push the changes to your repository"
  log "INFO" "2. Create a new Codespace or rebuild an existing one"
  log "INFO" "3. Verify that the Codespace has access to GCP resources"
}

# Execute main function
main