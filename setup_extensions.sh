#!/bin/bash
# setup_extensions.sh - Ensures VS Code extensions are installed and configured
# Created: May 1, 2025
# This script is automatically run by devcontainer.json's postStartCommand

set -e

EXTENSIONS=(
    # AI & Productivity
    "github.copilot"
    "codeium.codeium"
    "amazon.amazonq"
    "github.copilot-chat"
    
    # Python Development
    "ms-python.python"
    "ms-python.vscode-pylance"
    "charliermarsh.ruff"
    "ms-python.black-formatter"
    "kevinrose.vsc-python-indent"
    "njpwerner.autodocstring"
    "littlefoxteam.vscode-python-test-adapter"
    
    # Docker & Containerization
    "ms-azuretools.vscode-docker"
    "ms-vscode-remote.remote-containers"
    "formulahendry.docker-explorer"
    
    # GCP & Cloud
    "googlecloudtools.cloudcode"
    "GoogleCloudTools.cloudcode-cloudrun"
    "gcp-command-center.command-center"
    
    # Terraform & IaC
    "hashicorp.terraform"
    "run-at-scale.terraform-doc-snippets"
    "tfsec.tfsec"
    "erd0s.terraform-autocomplete"
    
    # CI/CD & Git
    "github.vscode-github-actions"
    "eamodio.gitlens"
    "github.vscode-pull-request-github"
    "bungcip.better-toml"
    
    # Miscellaneous
    "redhat.vscode-yaml"
    "ckolkman.vscode-postgres"
    "humao.rest-client"
    "streetsidesoftware.code-spell-checker"
    "usernamehw.errorlens"
    "ryanluker.vscode-coverage-gutters"
)

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Setting up VS Code extensions ===${NC}"

# Check if we're running in a container and if code CLI is available
if [ -z "$(which code)" ]; then
    echo -e "${YELLOW}VS Code CLI not available. We'll configure extensions in devcontainer.json only.${NC}"
    exit 0
fi

# Set up VS Code settings to avoid conflicts
mkdir -p /workspaces/orchestra-main/.vscode
SETTINGS_FILE="/workspaces/orchestra-main/.vscode/settings.json"

# Create settings file if it doesn't exist
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "{}" > "$SETTINGS_FILE"
fi

# Function to merge JSON settings
update_settings() {
    local key=$1
    local value=$2
    
    # Use python to update JSON (handles nested structures better than jq for this purpose)
    python3 -c "
import json, os
settings_file = '$SETTINGS_FILE'
with open(settings_file, 'r') as f:
    settings = json.load(f)
    
# Prepare the value (handle string vs objects)
try:
    value = json.loads('$value')
except:
    value = '$value'

# Get or create nested keys
keys = '$key'.split('.')
current = settings
for i, k in enumerate(keys[:-1]):
    if k not in current:
        current[k] = {}
    current = current[k]

# Set the value
current[keys[-1]] = value

# Write back
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=4)
"
}

# Configure optimal settings to avoid conflicts
update_settings "editor.formatOnSave" "true"
update_settings "editor.codeActionsOnSave" '{"source.fixAll": true, "source.organizeImports": true}'
update_settings "python.formatting.provider" "black"
update_settings "python.linting.enabled" "true"
update_settings "python.linting.lintOnSave" "true"
update_settings "python.defaultInterpreterPath" "${workspaceFolder}/.venv/bin/python"
update_settings "black-formatter.args" '["--line-length", "88"]'
update_settings "isort.args" '["--profile", "black"]'
update_settings "[python]" '{"editor.formatOnSave": true, "editor.defaultFormatter": "ms-python.black-formatter", "editor.formatOnType": true, "editor.rulers": [88], "editor.codeActionsOnSave": {"source.organizeImports": true}}'
update_settings "python.testing.pytestEnabled" "true"
update_settings "python.testing.unittestEnabled" "false"
update_settings "python.testing.nosetestsEnabled" "false"

# Install extensions if we have the code CLI available
for extension in "${EXTENSIONS[@]}"; do
    echo -e "${YELLOW}Ensuring extension is installed: $extension${NC}"
    code --install-extension "$extension" --force || echo -e "${YELLOW}Failed to install $extension - it will be installed via devcontainer.json${NC}"
done

# Verify Terraform CLI is available
if command -v terraform &> /dev/null; then
    echo -e "${GREEN}✓ Terraform CLI is installed ($(terraform version | head -n 1))${NC}"
    
    # Set up Terraform autocomplete
    terraform -install-autocomplete 2>/dev/null || echo "Terraform autocomplete already configured"
else
    echo -e "${YELLOW}⚠ Terraform CLI not found in PATH. Check your devcontainer configuration.${NC}"
fi

# Verify TFLint if available
if command -v tflint &> /dev/null; then
    echo -e "${GREEN}✓ TFLint is installed ($(tflint --version))${NC}"
    
    # Initialize TFLint if not already initialized
    if [ ! -f ".tflint.hcl" ]; then
        cat > .tflint.hcl << EOF
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}
EOF
        echo -e "${GREEN}✓ Created .tflint.hcl configuration${NC}"
    fi
else
    echo -e "${YELLOW}⚠ TFLint not found. Consider adding it to your devcontainer features.${NC}"
fi

# Verify GCP CLI is available
if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✓ Google Cloud SDK is installed ($(gcloud --version | head -n 1))${NC}"
    
    # Check if authorized
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
        echo -e "${GREEN}✓ GCP CLI is authenticated${NC}"
    else
        echo -e "${YELLOW}⚠ GCP CLI is not authenticated. Run 'gcloud auth login' when needed.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Google Cloud SDK not found in PATH. Check your configuration.${NC}"
fi

# Check Poetry configuration
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✓ Poetry is installed ($(poetry --version))${NC}"
    
    # Ensure virtualenvs.in-project is set to true
    if [ "$(poetry config virtualenvs.in-project)" != "true" ]; then
        poetry config virtualenvs.in-project true
        echo -e "${GREEN}✓ Set Poetry to use in-project virtualenvs${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Poetry not found in PATH. Check your configuration.${NC}"
fi

echo -e "${GREEN}=== VS Code extensions and configuration setup complete ===${NC}"
echo -e "${BLUE}💡 Tip: If any extensions aren't working correctly, try reloading the window (Ctrl+Shift+P > Developer: Reload Window)${NC}"

# Configure Cursor API key if available
if [ -n "$CURSOR_API_KEY" ]; then
  echo -e "${YELLOW}Configuring Cursor API key...${NC}"
  update_settings "cursor.apiKey" "$CURSOR_API_KEY"
fi

# Configure Claude Coder API key if available
if [ -n "$CLAUDE_CODER_API_KEY" ]; then
  echo -e "${YELLOW}Configuring Claude Coder API key...${NC}"
  update_settings "claudeCoder.apiKey" "$CLAUDE_CODER_API_KEY"
fi