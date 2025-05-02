#!/bin/bash
# Comprehensive script to permanently disable VS Code Restricted Mode in GitHub Codespaces
# This script implements multiple approaches to ensure Restricted Mode is fully disabled

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  COMPREHENSIVE VS CODE RESTRICTED MODE DISABLER${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Check if we're in a Codespace environment
if [ -z "$CODESPACES" ]; then
  echo -e "${YELLOW}Note: This doesn't appear to be a GitHub Codespace environment.${NC}"
  echo -e "${YELLOW}Some features may not work as expected.${NC}"
fi

# Function to create or update .vscode/settings.json
update_vscode_settings() {
  echo -e "\n${CYAN}[1/5]${NC} ${BOLD}Updating .vscode/settings.json...${NC}"
  
  # Create .vscode directory if it doesn't exist
  mkdir -p .vscode
  
  # Check if settings.json exists
  if [ -f .vscode/settings.json ]; then
    echo -e "${YELLOW}Existing settings.json found. Updating...${NC}"
    
    # Check if the file already has security.workspace.trust settings
    if grep -q "security.workspace.trust.enabled" .vscode/settings.json; then
      echo -e "${YELLOW}Workspace trust settings already exist in settings.json.${NC}"
      echo -e "${YELLOW}Ensuring they are set correctly...${NC}"
      
      # Use temporary file for in-place editing
      TMP_FILE=$(mktemp)
      
      # Try to use jq if available for proper JSON editing
      if command -v jq >/dev/null 2>&1; then
        jq '.["security.workspace.trust.enabled"] = false | 
            .["security.workspace.trust.startupPrompt"] = "never" | 
            .["security.workspace.trust.banner"] = "never" | 
            .["security.workspace.trust.emptyWindow"] = false' .vscode/settings.json > "$TMP_FILE"
        mv "$TMP_FILE" .vscode/settings.json
      else
        # Fallback to sed if jq is not available (less reliable)
        sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' .vscode/settings.json
        sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' .vscode/settings.json
        sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' .vscode/settings.json
        sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' .vscode/settings.json
      fi
    else
      # Settings exist but no workspace trust settings yet
      echo -e "${YELLOW}Adding workspace trust settings to existing settings.json...${NC}"
      
      # Use temporary file for in-place editing
      TMP_FILE=$(mktemp)
      
      # Try to use jq if available for proper JSON editing
      if command -v jq >/dev/null 2>&1; then
        jq '. + {
          "security.workspace.trust.enabled": false,
          "security.workspace.trust.startupPrompt": "never",
          "security.workspace.trust.banner": "never",
          "security.workspace.trust.emptyWindow": false
        }' .vscode/settings.json > "$TMP_FILE"
        mv "$TMP_FILE" .vscode/settings.json
      else
        # Fallback to basic append (might break JSON structure)
        # Remove the last closing brace
        sed -i '$ s/}$/,/' .vscode/settings.json
        # Append the new settings
        cat << EOF >> .vscode/settings.json
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
      fi
    fi
  else
    # Create new settings.json
    echo -e "${YELLOW}Creating new settings.json with workspace trust settings...${NC}"
    cat << EOF > .vscode/settings.json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
  fi
  
  echo -e "${GREEN}✓ .vscode/settings.json updated successfully.${NC}"
}

# Function to update devcontainer.json
update_devcontainer() {
  echo -e "\n${CYAN}[2/5]${NC} ${BOLD}Updating devcontainer.json...${NC}"
  
  # Check if devcontainer.json exists
  if [ -f .devcontainer/devcontainer.json ]; then
    echo -e "${YELLOW}Existing devcontainer.json found. Updating...${NC}"
    
    # Check if devcontainer.json already has workspace trust settings
    if grep -q "security.workspace.trust.enabled" .devcontainer/devcontainer.json; then
      echo -e "${YELLOW}Workspace trust settings already exist in devcontainer.json.${NC}"
      echo -e "${GREEN}✓ No changes needed.${NC}"
    else
      echo -e "${YELLOW}Adding workspace trust settings to devcontainer.json...${NC}"
      
      # Try to use jq if available for proper JSON editing
      if command -v jq >/dev/null 2>&1; then
        TMP_FILE=$(mktemp)
        
        # If customizations.vscode.settings exists, add to it
        if jq -e '.customizations.vscode.settings' .devcontainer/devcontainer.json >/dev/null 2>&1; then
          jq '.customizations.vscode.settings += {
            "security.workspace.trust.enabled": false,
            "security.workspace.trust.startupPrompt": "never",
            "security.workspace.trust.banner": "never",
            "security.workspace.trust.emptyWindow": false
          }' .devcontainer/devcontainer.json > "$TMP_FILE"
          mv "$TMP_FILE" .devcontainer/devcontainer.json
          echo -e "${GREEN}✓ Added settings to existing customizations.vscode.settings.${NC}"
        else
          # Structure doesn't exist, so we need to create it
          echo -e "${YELLOW}Could not find customizations.vscode.settings section.${NC}"
          echo -e "${YELLOW}You may need to manually update devcontainer.json.${NC}"
          echo -e "${YELLOW}Please add the following to your devcontainer.json in the appropriate location:${NC}"
          echo -e "\"customizations\": {"
          echo -e "  \"vscode\": {"
          echo -e "    \"settings\": {"
          echo -e "      \"security.workspace.trust.enabled\": false,"
          echo -e "      \"security.workspace.trust.startupPrompt\": \"never\","
          echo -e "      \"security.workspace.trust.banner\": \"never\","
          echo -e "      \"security.workspace.trust.emptyWindow\": false"
          echo -e "    }"
          echo -e "  }"
          echo -e "}"
        fi
      else
        echo -e "${YELLOW}jq not found. Manual intervention required.${NC}"
        echo -e "${YELLOW}Please manually add the workspace trust settings to devcontainer.json.${NC}"
      fi
    fi
  else
    echo -e "${YELLOW}No devcontainer.json found in .devcontainer directory.${NC}"
    echo -e "${YELLOW}This may not be a Codespace or doesn't use devcontainer.${NC}"
  fi
}

# Function to create VS Code CLI command file
create_vscode_cli_command() {
  echo -e "\n${CYAN}[3/5]${NC} ${BOLD}Creating VS Code CLI command file...${NC}"
  
  # Create a script that uses VS Code CLI to disable workspace trust
  cat << 'EOF' > .vscode/disable_trust.js
// This script disables VS Code workspace trust using the VS Code API
// You can run this from the Command Palette: "Developer: Open Webview Developer Tools"
// Then paste this in the Console

(function() {
  try {
    // Access the VS Code API
    const vscode = acquireVsCodeApi();
    
    // Send message to extension host to disable workspace trust
    vscode.postMessage({
      command: 'workspaceTrust',
      action: 'disable'
    });
    
    // Try to directly modify the workspace trust settings
    // This is a backup approach and may not work in all VS Code versions
    const settings = {
      "security.workspace.trust.enabled": false,
      "security.workspace.trust.startupPrompt": "never",
      "security.workspace.trust.banner": "never",
      "security.workspace.trust.emptyWindow": false
    };
    
    // Use localStorage to persist these settings
    for (const [key, value] of Object.entries(settings)) {
      localStorage.setItem(`vscode.${key}`, JSON.stringify(value));
    }
    
    console.log('Workspace trust disabled successfully');
  } catch (error) {
    console.error('Failed to disable workspace trust:', error);
  }
})();
EOF
  
  echo -e "${GREEN}✓ Created .vscode/disable_trust.js${NC}"
  echo -e "${YELLOW}Note: You can use this script in VS Code's Developer Console if other methods fail.${NC}"
}

# Function to add VS Code arguments to workspace file
update_workspace_file() {
  echo -e "\n${CYAN}[4/5]${NC} ${BOLD}Checking for workspace file...${NC}"
  
  # Look for .code-workspace files
  WORKSPACE_FILES=$(find . -maxdepth 1 -name "*.code-workspace" -type f)
  
  if [ -n "$WORKSPACE_FILES" ]; then
    echo -e "${YELLOW}Found workspace file(s):${NC}"
    
    for file in $WORKSPACE_FILES; do
      echo -e "${YELLOW}  - $file${NC}"
      
      # Check if file already has trust settings
      if grep -q "security.workspace.trust.enabled" "$file"; then
        echo -e "${YELLOW}  Workspace trust settings already exist in $file.${NC}"
      else
        echo -e "${YELLOW}  Adding workspace trust settings to $file...${NC}"
        
        # Try to use jq if available for proper JSON editing
        if command -v jq >/dev/null 2>&1; then
          TMP_FILE=$(mktemp)
          
          # If settings exists, add to it
          if jq -e '.settings' "$file" >/dev/null 2>&1; then
            jq '.settings += {
              "security.workspace.trust.enabled": false,
              "security.workspace.trust.startupPrompt": "never",
              "security.workspace.trust.banner": "never",
              "security.workspace.trust.emptyWindow": false
            }' "$file" > "$TMP_FILE"
            mv "$TMP_FILE" "$file"
            echo -e "${GREEN}  ✓ Added settings to existing settings in $file.${NC}"
          else
            # Add settings section
            jq '. += {
              "settings": {
                "security.workspace.trust.enabled": false,
                "security.workspace.trust.startupPrompt": "never",
                "security.workspace.trust.banner": "never",
                "security.workspace.trust.emptyWindow": false
              }
            }' "$file" > "$TMP_FILE"
            mv "$TMP_FILE" "$file"
            echo -e "${GREEN}  ✓ Added settings section to $file.${NC}"
          fi
        else
          echo -e "${YELLOW}  jq not found. Manual intervention required.${NC}"
          echo -e "${YELLOW}  Please manually add workspace trust settings to $file.${NC}"
        fi
      fi
    done
  else
    echo -e "${YELLOW}No .code-workspace files found.${NC}"
  fi
}

# Function to set environment variables for VS Code
set_environment_vars() {
  echo -e "\n${CYAN}[5/5]${NC} ${BOLD}Setting environment variables...${NC}"
  
  # Create or update .bashrc to set environment variables
  if [ -f ~/.bashrc ]; then
    echo -e "${YELLOW}Updating ~/.bashrc with environment variables...${NC}"
    
    # Remove any existing VS Code workspace trust variables
    grep -v "VSCODE_DISABLE_WORKSPACE_TRUST" ~/.bashrc > ~/.bashrc.tmp
    mv ~/.bashrc.tmp ~/.bashrc
    
    # Add the environment variables
    cat << 'EOF' >> ~/.bashrc

# VS Code workspace trust environment variables
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
EOF
    
    echo -e "${GREEN}✓ Added environment variables to ~/.bashrc${NC}"
    echo -e "${YELLOW}Note: You'll need to restart your shell or run 'source ~/.bashrc' for these to take effect.${NC}"
  else
    echo -e "${YELLOW}No ~/.bashrc found. Creating one...${NC}"
    
    # Create .bashrc with environment variables
    cat << 'EOF' > ~/.bashrc
# VS Code workspace trust environment variables
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
EOF
    
    echo -e "${GREEN}✓ Created ~/.bashrc with environment variables${NC}"
    echo -e "${YELLOW}Note: You'll need to restart your shell or run 'source ~/.bashrc' for these to take effect.${NC}"
  fi
  
  # Set variables for current session
  export VSCODE_DISABLE_WORKSPACE_TRUST=true
  export DISABLE_WORKSPACE_TRUST=true
  
  echo -e "${GREEN}✓ Set environment variables for current session${NC}"
}

# Execute all functions
update_vscode_settings
update_devcontainer
create_vscode_cli_command
update_workspace_file
set_environment_vars

echo -e "\n${BOLD}${GREEN}=====================================================${NC}"
echo -e "${BOLD}${GREEN}  RESTRICTED MODE SHOULD NOW BE PERMANENTLY DISABLED${NC}"
echo -e "${BOLD}${GREEN}=====================================================${NC}"
echo -e "\n${BOLD}${BLUE}To fully apply these changes, you should:${NC}"
echo -e "${YELLOW}1. Run 'source ~/.bashrc' to apply environment variables${NC}"
echo -e "${YELLOW}2. Restart VS Code: Command Palette > Developer: Reload Window${NC}"
echo -e "${YELLOW}3. If issues persist, rebuild the Codespace: Command Palette > Codespaces: Rebuild Container${NC}"
echo -e "\n${BOLD}${BLUE}For additional debugging:${NC}"
echo -e "${YELLOW}1. Check VS Code logs: Help > Toggle Developer Tools > Console${NC}"
echo -e "${YELLOW}2. Try opening VS Code with the --disable-workspace-trust flag${NC}"
echo -e "${YELLOW}3. Run VS Code with verbose logging: code --verbose${NC}"

# Provide command line option for launching code with disable-workspace-trust
echo -e "\n${BOLD}${BLUE}Command line alternative:${NC}"
echo -e "${YELLOW}code . --disable-workspace-trust${NC}"
