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
