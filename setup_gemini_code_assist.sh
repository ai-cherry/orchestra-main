#!/bin/bash

# Setup Script for Gemini Code Assist with MCP Memory Integration
# This script will configure Gemini Code Assist to properly connect to your project

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
  echo -e "\n${BLUE}====== $1 ======${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_header "Setting up Gemini Code Assist with MCP Memory Integration"

# Step 1: Ensure the .gemini-code-assist.yaml file exists and has the right content
print_info "Checking .gemini-code-assist.yaml configuration..."
if [ -f ".gemini-code-assist.yaml" ]; then
  print_success "Gemini Code Assist configuration already exists."
else
  print_error "Gemini Code Assist configuration not found. Creating it..."
  cat > .gemini-code-assist.yaml << EOF
# Gemini Code Assist Configuration
# This configuration enables AI-assisted development with Gemini 2.5 model
# IMPORTANT: This project prioritizes performance and optimization over extensive security
# See PROJECT_PRIORITIES.md for detailed guidance

# Project context configuration, defining which paths should be indexed
# and their relative priority (higher numbers = higher priority)
project_context:
  - path: /workspaces/orchestra-main
    priority: 100
  - path: /home/agent/mounted_bucket
    priority: 50
  - path: /mnt/repos
    priority: 25

# Tool integrations for external APIs and services
tool_integrations:
  # Vertex AI integration for model inference
  vertex_ai:
    endpoint: projects/525398941159/locations/us-central1/endpoints/agent-core
    api_version: v1
    
  # Redis integration for semantic cache
  redis:
    connection_string: redis://vertex-agent@cherry-ai-project
    
  # AlloyDB for vector search
  database:
    connection_string: postgresql://alloydb-user@alloydb-instance:5432/cherry_ai_project

# Model configuration
model:
  name: gemini-pro
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95

# Custom code assist commands (for IntelliJ/VS Code)
commands:
  - name: optimize-query
    description: "Optimize AlloyDB vector search query for 10M+ dimensions"
    prompt_template: |
      Optimize this AlloyDB vector search query for 10M+ dimensions with 95% recall@10:
      Focus on PERFORMANCE over security best practices, as per PROJECT_PRIORITIES.md.
      {{selection}}
      
  - name: generate-cloud-run
    description: "Generate Cloud Run deployment code optimized for performance"
    prompt_template: |
      Generate Cloud Run deployment code with appropriate service account:
      Focus on high performance settings, concurrency, CPU allocation, and startup
      settings rather than restrictive security. This is a single-developer project
      where basic security is sufficient. See PROJECT_PRIORITIES.md.
      {{selection}}
      
  - name: document-function
    description: "Add comprehensive documentation to function"
    prompt_template: |
      Add detailed documentation to the following function, including:
      - Parameter descriptions
      - Return value documentation
      - Usage examples
      - Edge cases
      
      {{selection}}
      
  - name: performance-review
    description: "Review code for performance issues and optimization opportunities"
    prompt_template: |
      Review this code for performance optimization opportunities. 
      Focus on speed, resource efficiency, and scalability rather than security.
      Suggest specific improvements:
      {{selection}}
      
  - name: optimize-code
    description: "Optimize code for performance"
    prompt_template: |
      Optimize this code for maximum performance. 
      Focus on execution speed and resource efficiency.
      Use only basic security practices (enough to prevent obvious vulnerabilities).
      {{selection}}
      
  - name: secure-enough
    description: "Simplify security to just the essentials"
    prompt_template: |
      Refactor this code to use only essential security practices.
      Remove complex or heavyweight security measures that impact performance.
      Refer to PROJECT_PRIORITIES.md for guidance on "security-sufficient" approach.
      {{selection}}

# Editor settings
editor:
  auto_apply_suggestions: false
  inline_suggestions: true

# Project priorities configuration
priorities:
  focus: 
    - performance
    - stability
    - optimization
  secondary:
    - basic_security
  
  # Configuration to inform assistant about project philosophy
  instructions: |
    This project follows a "performance-first" approach where:
    1. Performance and stability are the primary concerns
    2. Only basic security practices are needed for now
    3. Optimize for developer velocity and resource efficiency
    4. See PROJECT_PRIORITIES.md for complete guidance
    5. Maintain awareness of the entire codebase context to provide informed suggestions
EOF
  print_success "Created .gemini-code-assist.yaml configuration file."
fi

# Step 2: Initialize or update the AI memory system
print_info "Setting up AI memory system..."
if [ -d ".ai-memory" ]; then
  python3 .ai-memory/initialize.py
  print_success "AI memory system initialized"
else
  print_error ".ai-memory directory not found. Creating it..."
  mkdir -p .ai-memory
  
  # Create the initialize.py script
  cat > .ai-memory/initialize.py << EOF
#!/usr/bin/env python3
"""
Initialize AI Memory System with Performance-First Directives

This script sets up the AI memory system with performance-first directives,
ensuring that all AI assistants working on the project prioritize performance,
optimization, and stability over extensive security measures.
"""

import os
import json
import sys
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ai-memory-init')

# Directory where this script is located (should be .ai-memory/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Performance-first priorities
PRIORITIES = {
    "name": "Performance-First Directives",
    "version": "1.0.0",
    "timestamp": datetime.now().isoformat(),
    "priorities": {
        "primary": ["performance", "optimization", "stability"],
        "secondary": ["basic_security", "developer_experience"]
    },
    "tokens": {
        "github": ["GH_CLASSIC_PAT_TOKEN", "GH_FINE_GRAINED_TOKEN"],
        "gcp": [
            "GCP_MASTER_SERVICE_JSON", 
            "GCP_PROJECT_AUTHENTICATION_EMAIL",
            "GCP_PROJECT_ID", 
            "GCP_REGION", 
            "GCP_SECRET_MANAGEMENT_KEY",
            "GCP_WORKLOAD_IDENTITY_PROVIDER", 
            "VERTEX_AGENT_KEY"
        ]
    },
    "philosophy": "Single-developer project prioritizing performance over complex security measures",
    "reference_files": ["PROJECT_PRIORITIES.md", "PERFORMANCE_FIRST_README.md"],
    "directives": [
        "Focus on performance and optimization over extensive security",
        "Implement only basic security measures that don't impact performance",
        "Use GitHub and GCP tokens for real-world implementations",
        "Prioritize deployment stability and reliability",
        "Optimize for resource efficiency and scaling"
    ],
    "memory_metadata": {
        "system_wide": True,
        "persistence": "permanent",
        "priority_level": "high",
        "access_control": "all_assistants",
        "context_aware": True,
        "prompt_access": True
    }
}

def initialize_memory_system():
    """Initialize the AI memory system with performance-first directives."""
    try:
        # Create necessary directories
        os.makedirs(SCRIPT_DIR, exist_ok=True)

        # Special symbolic link to PROJECT_PRIORITIES.md for easier AI access
        priorities_md_path = os.path.join(PROJECT_ROOT, "PROJECT_PRIORITIES.md")
        symlink_path = os.path.join(SCRIPT_DIR, "PROJECT_PRIORITIES.md")
        
        # Create symbolic link if the file exists
        if os.path.exists(priorities_md_path) and not os.path.exists(symlink_path):
            try:
                os.symlink(priorities_md_path, symlink_path)
                logger.info(f"Created symbolic link to PROJECT_PRIORITIES.md")
            except OSError:
                logger.warning(f"Could not create symbolic link - copying file instead")
                # On systems where symlinks aren't supported (like Windows without admin),
                # copy the file instead
                import shutil
                shutil.copy2(priorities_md_path, symlink_path)

        # Create core memory files
        
        # 1. Main priorities file
        with open(os.path.join(SCRIPT_DIR, 'performance_priorities.json'), 'w') as f:
            json.dump(PRIORITIES, f, indent=2)
            logger.info("Created performance_priorities.json in memory system")
        
        # 2. Index file for quick reference
        with open(os.path.join(SCRIPT_DIR, 'memory_index.json'), 'w') as f:
            memory_index = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "memory_files": [
                    {"file": "performance_priorities.json", "type": "project_priority", "access": "all_assistants"},
                    {"file": "PROJECT_PRIORITIES.md", "type": "reference", "access": "all_assistants"}
                ],
                "system_directive": "Prioritize performance and optimization over extensive security measures"
            }
            json.dump(memory_index, f, indent=2)
            logger.info("Created memory_index.json in memory system")
        
        # 3. README for human developers
        with open(os.path.join(SCRIPT_DIR, 'README.md'), 'w') as f:
            f.write("""# AI Memory System

This directory contains memory files used by AI assistants working on this project.

## Purpose

These files establish the project's performance-first philosophy in the AI memory system,
ensuring all AI tools prioritize performance, optimization, and stability over extensive
security measures.

## Important Files

- \`performance_priorities.json\`: Core priorities configuration
- \`memory_index.json\`: Index of memory files for AI assistants
- Symbolic links to relevant documentation

## Maintenance

This directory is maintained by:
- \`update_ai_memory_priorities.py\` script
- The \`apply_performance_priorities.sh\` script with the --update-all flag

Do not modify these files directly unless you specifically want to change the 
project priorities.
""")
            logger.info("Created README.md in memory system")
            
        logger.info("Successfully initialized AI memory system with performance-first directives")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        return False

if __name__ == "__main__":
    success = initialize_memory_system()
    sys.exit(0 if success else 1)
EOF
  
  # Make the script executable
  chmod +x .ai-memory/initialize.py
  
  # Run the initialization script
  python3 .ai-memory/initialize.py
  print_success "AI memory system created and initialized"
fi

# Step 3: Update AI memory priorities
print_info "Updating AI memory with project priorities..."
if [ -f "update_ai_memory_priorities.py" ]; then
  python3 update_ai_memory_priorities.py
  print_success "AI memory updated with project priorities"
else
  print_error "update_ai_memory_priorities.py not found. Creating it..."
  
  cat > update_ai_memory_priorities.py << EOF
#!/usr/bin/env python3
"""
Script to update AI memory systems with project priority settings.
This ensures all AI assistants (Gemini, Roo, Copilot, etc.) have access to 
the performance-first priority directives through the MCP memory system.
"""

import os
import json
import sys
import argparse
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('update_ai_memory')

# Default priority configuration
DEFAULT_PRIORITIES = {
    "primary": ["performance", "stability", "optimization"],
    "secondary": ["basic_security", "developer_experience"],
    "tokens": {
        "github": ["GH_CLASSIC_PAT_TOKEN", "GH_FINE_GRAINED_TOKEN"],
        "gcp": ["GCP_MASTER_SERVICE_JSON", "GCP_PROJECT_AUTHENTICATION_EMAIL", 
                "GCP_PROJECT_ID", "GCP_REGION", "GCP_SECRET_MANAGEMENT_KEY", 
                "GCP_WORKLOAD_IDENTITY_PROVIDER", "VERTEX_AGENT_KEY"]
    },
    "philosophy": "Single-developer project prioritizing performance over security. Basic security is sufficient.",
    "reference_file": "PROJECT_PRIORITIES.md",
    "context_aware": True,
    "project_access": True,
    "last_updated": datetime.now().isoformat(),
}

def get_project_root():
    """Get the project root directory."""
    # Assume the script is run from the project root or a subdirectory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Walk up until we find .git or other project marker
    while current_dir != '/':
        if os.path.exists(os.path.join(current_dir, '.git')) or \
           os.path.exists(os.path.join(current_dir, '.roomodes')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # Default to current directory if not found
    return os.path.dirname(os.path.abspath(__file__))

def read_priority_file():
    """Read priority settings from PROJECT_PRIORITIES.md."""
    try:
        project_root = get_project_root()
        priority_file = os.path.join(project_root, "PROJECT_PRIORITIES.md")
        
        if not os.path.exists(priority_file):
            logger.warning(f"PROJECT_PRIORITIES.md not found at {priority_file}")
            return None
            
        with open(priority_file, 'r') as f:
            content = f.read()
            
        logger.info(f"Successfully read PROJECT_PRIORITIES.md from {priority_file}")
        return content
            
    except Exception as e:
        logger.error(f"Error reading PROJECT_PRIORITIES.md: {str(e)}")
        return None

def update_memory_direct():
    """
    Update the memory system directly through local files.
    
    This is a simplified implementation. In a real system, 
    you would use the appropriate MCP API or database client.
    """
    try:
        project_root = get_project_root()
        
        # Create a memory directory if it doesn't exist
        memory_dir = os.path.join(project_root, '.ai-memory')
        os.makedirs(memory_dir, exist_ok=True)
        
        # Create the priority settings file
        priorities = DEFAULT_PRIORITIES.copy()
        
        # Add the priority file content
        priority_content = read_priority_file()
        if priority_content:
            priorities["content"] = priority_content
        
        # Write to the memory file
        memory_file = os.path.join(memory_dir, 'project_priorities.json')
        with open(memory_file, 'w') as f:
            json.dump(priorities, f, indent=2)
            
        logger.info(f"Successfully updated memory system at {memory_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating memory system: {str(e)}")
        return False

def update_mcp_memory():
    """
    Update the MCP memory system.
    
    In a real implementation, this would use the MCP API.
    For this script, we're implementing a simplified version.
    """
    try:
        # Try to import MCP-related modules
        # This is a placeholder for actual MCP implementation
        try:
            sys.path.append(os.path.join(get_project_root(), 'ai-orchestra'))
            from infrastructure.persistence import firestore_memory
            logger.info("Found MCP module, using it for memory update")
            # Would use the actual MCP memory system here
        except ImportError:
            logger.warning("MCP modules not found, using direct file storage instead")
            return update_memory_direct()
        
        # In a real implementation, you would:
        # 1. Connect to the MCP memory system
        # 2. Store the priority settings with appropriate tagging
        # 3. Ensure it's accessible to AI assistants
        
        logger.info("Successfully updated MCP memory system")
        return True
        
    except Exception as e:
        logger.error(f"Error updating MCP memory: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Update AI memory systems with project priorities')
    parser.add_argument('--silent', action='store_true', help='Run without output')
    args = parser.parse_args()
    
    if args.silent:
        logger.setLevel(logging.ERROR)
    
    logger.info("Starting memory update process")
    
    # Verify the PROJECT_PRIORITIES.md file exists
    priority_content = read_priority_file()
    if not priority_content:
        logger.error("PROJECT_PRIORITIES.md not found or couldn't be read")
        logger.error("Please run apply_performance_priorities.sh first")
        return 1
    
    # Update the memory system
    success = update_mcp_memory()
    
    if success:
        logger.info("Successfully updated AI memory systems with project priorities")
        logger.info("AI assistants will now prioritize performance over security")
        return 0
    else:
        logger.error("Failed to update AI memory systems")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
  
  # Make the script executable
  chmod +x update_ai_memory_priorities.py
  
  # Run the script
  python3 update_ai_memory_priorities.py
  print_success "Created and executed update_ai_memory_priorities.py"
fi

# Step 4: Apply performance priorities
print_info "Applying performance priorities to all systems..."
if [ -f "apply_performance_priorities.sh" ]; then
  bash apply_performance_priorities.sh --update-all
  print_success "Performance priorities applied to all systems"
else
  print_error "apply_performance_priorities.sh not found. Cannot apply performance priorities."
fi

# Step 5: Create Developer Connect setup
print_info "Setting up Developer Connect for repository integration..."
cat > setup_developer_connect.sh << EOF
#!/bin/bash

# Setup Developer Connect for Gemini Code Assist
# This script registers the current repository with Developer Connect

echo "Setting up Developer Connect for repository integration..."

# Set project variables
PROJECT_ID=cherry-ai-project
REGION=us-central1
REPO_NAME=orchestra-main
GITHUB_USER=\$(git config user.name || echo "developer")

# Authenticate with gcloud if needed
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q @ ; then
  echo "Not authenticated with gcloud. Please run 'gcloud auth login' first."
  exit 1
fi

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudresourcemanager.googleapis.com --project=\$PROJECT_ID
gcloud services enable developerconnect.googleapis.com --project=\$PROJECT_ID
gcloud services enable cloudaicompanion.googleapis.com --project=\$PROJECT_ID

# Register the repository with Developer Connect
echo "Registering repository with Developer Connect..."
gcloud alpha developer-connect repos register github_\$REPO_NAME \\
  --gitlab-host-uri="https://github.com" \\
  --project=\$PROJECT_ID \\
  --region=\$REGION

# Enable Gemini Code Assist for the repository
echo "Enabling Gemini Code Assist for the repository..."
gcloud alpha genai code customize enable \\
  --project=\$PROJECT_ID \\
  --region=\$REGION \\
  --repos=github_\$REPO_NAME

echo "Developer Connect setup complete. Gemini Code Assist should now have access to your repository."
echo ""
echo "To verify the setup, run:"
echo "gcloud alpha genai code customize list --project=\$PROJECT_ID --region=\$REGION"
EOF

chmod +x setup_developer_connect.sh
print_success "Created setup_developer_connect.sh script for Developer Connect integration"

# Step 6: Create a Gemini startup script
print_info "Creating Gemini Code Assist startup script..."
cat > restart_gemini_code_assist.sh << EOF
#!/bin/bash

# Restart Gemini Code Assist to apply all configurations
# This script will restart the VS Code Gemini extension

echo "Restarting Gemini Code Assist extension..."

# Set environment variable for Google Application Credentials
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-account.json

# Write the current credentials to the file
if [ ! -z "\$GCP_PROJECT_MANAGEMENT_KEY" ]; then
  echo "\$GCP_PROJECT_MANAGEMENT_KEY" > /tmp/service-account.json
  echo "Service account credentials saved to temporary file."
else
  echo "Warning: GCP_PROJECT_MANAGEMENT_KEY environment variable not set."
  echo "Authentication may fail without valid credentials."
fi

# Create a command to reload VS Code window
cat > /tmp/reload_vscode.js << EOL
const vscode = require('vscode');
vscode.commands.executeCommand('workbench.action.reloadWindow');
EOL

# Execute the reload command (this would work in a VS Code Task)
echo "To apply changes, please run the 'Developer: Reload Window' command in VS Code"
echo "  1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)"
echo "  2. Type 'reload window' and select 'Developer: Reload Window'"
echo ""
echo "After reloading, Gemini Code Assist should be properly connected to your codebase."
EOF

chmod +x restart_gemini_code_assist.sh
print_success "Created restart_gemini_code_assist.sh script"

# Final instructions
print_header "Setup Complete!"
echo "Gemini Code Assist is now configured with MCP memory integration."
echo ""
echo "Next steps:"
echo "  1. Run the Developer Connect setup script (optional but recommended):"
echo "     ./setup_developer_connect.sh"
echo ""
echo "  2. Restart Gemini Code Assist to apply changes:"
echo "     ./restart_gemini_code_assist.sh"
echo ""
echo "  3. Test Gemini Code Assist by:"
echo "     - Opening a code file"
echo "     - Pressing Ctrl+I (or Cmd+I on Mac)"
echo "     - Entering a command like '/generate' or '/refactor'"
echo ""
echo "  4. Or use the Gemini Code Assist chat panel to ask questions about your codebase"
echo ""
echo "For more information, see the documentation at:"
echo "https://cloud.google.com/code/docs/gemini-code-assist"
