#!/bin/bash
# disable_restrictions.sh - Script to disable VS Code security features
# For single-developer, single-user projects to improve development velocity

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Simple logging function
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
  exit 1
}

# Find VS Code settings file
find_settings_file() {
  local settings_paths=(".vscode/settings.json" "../.vscode/settings.json" "../../.vscode/settings.json" "$HOME/.config/Code/User/settings.json" "$HOME/Library/Application Support/Code/User/settings.json" "$APPDATA/Code/User/settings.json")
  
  for path in "${settings_paths[@]}"; do
    if [ -f "$path" ]; then
      echo "$path"
      return 0
    fi
  done
  
  return 1
}

# Disable workspace trust feature
disable_workspace_trust() {
  log "Disabling VS Code workspace trust feature..."
  
  local settings_file=$(find_settings_file)
  
  if [ -z "$settings_file" ]; then
    warn "VS Code settings file not found. Creating a new one in .vscode/settings.json"
    mkdir -p .vscode
    settings_file=".vscode/settings.json"
    echo "{}" > "$settings_file"
  fi
  
  # Check if file is valid JSON
  if ! jq empty "$settings_file" 2>/dev/null; then
    warn "Settings file is not valid JSON. Creating a backup and starting fresh."
    cp "$settings_file" "${settings_file}.bak"
    echo "{}" > "$settings_file"
  fi
  
  # Add workspace trust settings
  log "Updating settings file: $settings_file"
  
  # Use jq to update settings if available
  if command -v jq &>/dev/null; then
    local temp_file=$(mktemp)
    jq '. + {
      "security.workspace.trust.enabled": false,
      "security.workspace.trust.startupPrompt": "never",
      "security.workspace.trust.banner": "never",
      "security.workspace.trust.emptyWindow": false,
      "security.workspace.trust.untrustedFiles": "open"
    }' "$settings_file" > "$temp_file"
    mv "$temp_file" "$settings_file"
  else
    # Fallback to simple sed-based approach
    warn "jq not found, using simple text replacement"
    
    # Create backup
    cp "$settings_file" "${settings_file}.bak"
    
    # Remove closing brace if it exists
    sed -i.tmp 's/}$//' "$settings_file"
    
    # Add our settings
    cat >> "$settings_file" <<EOL
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false,
  "security.workspace.trust.untrustedFiles": "open"
}
EOL
    # Clean up
    rm -f "${settings_file}.tmp"
  fi
  
  log "Workspace trust feature disabled successfully"
}

# Disable extension security restrictions
disable_extension_restrictions() {
  log "Disabling VS Code extension security restrictions..."
  
  local settings_file=$(find_settings_file)
  
  if [ -z "$settings_file" ]; then
    error "VS Code settings file not found"
  fi
  
  # Use jq to update settings if available
  if command -v jq &>/dev/null; then
    local temp_file=$(mktemp)
    jq '. + {
      "extensions.autoUpdate": false,
      "extensions.autoCheckUpdates": false,
      "extensions.ignoreRecommendations": true,
      "extensions.verifySignature": false
    }' "$settings_file" > "$temp_file"
    mv "$temp_file" "$settings_file"
  else
    # Fallback to simple sed-based approach
    warn "jq not found, using simple text replacement"
    
    # Create backup
    cp "$settings_file" "${settings_file}.bak"
    
    # Remove closing brace if it exists
    sed -i.tmp 's/}$//' "$settings_file"
    
    # Add our settings
    cat >> "$settings_file" <<EOL
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "extensions.ignoreRecommendations": true,
  "extensions.verifySignature": false
}
EOL
    # Clean up
    rm -f "${settings_file}.tmp"
  fi
  
  log "Extension security restrictions disabled successfully"
}

# Disable telemetry
disable_telemetry() {
  log "Disabling VS Code telemetry..."
  
  local settings_file=$(find_settings_file)
  
  if [ -z "$settings_file" ]; then
    error "VS Code settings file not found"
  fi
  
  # Use jq to update settings if available
  if command -v jq &>/dev/null; then
    local temp_file=$(mktemp)
    jq '. + {
      "telemetry.enableTelemetry": false,
      "telemetry.enableCrashReporter": false,
      "workbench.enableExperiments": false,
      "workbench.settings.enableNaturalLanguageSearch": false
    }' "$settings_file" > "$temp_file"
    mv "$temp_file" "$settings_file"
  else
    # Fallback to simple sed-based approach
    warn "jq not found, using simple text replacement"
    
    # Create backup
    cp "$settings_file" "${settings_file}.bak"
    
    # Remove closing brace if it exists
    sed -i.tmp 's/}$//' "$settings_file"
    
    # Add our settings
    cat >> "$settings_file" <<EOL
  "telemetry.enableTelemetry": false,
  "telemetry.enableCrashReporter": false,
  "workbench.enableExperiments": false,
  "workbench.settings.enableNaturalLanguageSearch": false
}
EOL
    # Clean up
    rm -f "${settings_file}.tmp"
  fi
  
  log "Telemetry disabled successfully"
}

# Main function
main() {
  log "Starting VS Code security restrictions removal..."
  
  # Disable workspace trust
  disable_workspace_trust
  
  # Disable extension restrictions
  disable_extension_restrictions
  
  # Disable telemetry
  disable_telemetry
  
  log "All VS Code security restrictions have been disabled!"
  log "Note: You may need to restart VS Code for changes to take effect."
  log "For a complete development experience, also consider running:"
  log "  - simplified_deploy.sh: For streamlined deployments"
  log "  - python mcp_server/run_optimized_server.py: For optimized MCP server"
}

# Execute main function
main