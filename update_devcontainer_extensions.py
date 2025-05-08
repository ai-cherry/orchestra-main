#!/usr/bin/env python3
"""
update_devcontainer_extensions.py - Update devcontainer.json with critical extensions

This script reads the extensions.json file and updates the devcontainer.json file
with the critical extensions. This ensures that only essential extensions are
installed during container creation, improving startup performance.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Configuration
EXTENSIONS_CONFIG = "extensions.json"
DEVCONTAINER_PATH = ".devcontainer/devcontainer.json"


def load_extensions_config(config_path: str) -> Dict[str, List[str]]:
    """
    Load extensions configuration from JSON file.
    
    Args:
        config_path: Path to the extensions configuration file
        
    Returns:
        Dictionary containing extension categories and their extensions
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the configuration file is not valid JSON
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Extensions configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Extensions configuration file is not valid JSON: {config_path}")
        sys.exit(1)


def load_devcontainer_config(devcontainer_path: str) -> Dict[str, Any]:
    """
    Load devcontainer configuration from JSON file.
    
    Args:
        devcontainer_path: Path to the devcontainer.json file
        
    Returns:
        Dictionary containing devcontainer configuration
        
    Raises:
        FileNotFoundError: If the devcontainer file doesn't exist
        json.JSONDecodeError: If the devcontainer file is not valid JSON
    """
    try:
        with open(devcontainer_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Devcontainer file not found: {devcontainer_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Devcontainer file is not valid JSON: {devcontainer_path}")
        sys.exit(1)


def update_devcontainer(
    devcontainer: Dict[str, Any], 
    critical_extensions: List[str]
) -> Dict[str, Any]:
    """
    Update devcontainer configuration with critical extensions.
    
    Args:
        devcontainer: Devcontainer configuration dictionary
        critical_extensions: List of critical extensions to include
        
    Returns:
        Updated devcontainer configuration dictionary
    """
    # Ensure customizations section exists
    if 'customizations' not in devcontainer:
        devcontainer['customizations'] = {}
    
    # Ensure vscode section exists
    if 'vscode' not in devcontainer['customizations']:
        devcontainer['customizations']['vscode'] = {}
    
    # Update extensions
    devcontainer['customizations']['vscode']['extensions'] = critical_extensions
    
    return devcontainer


def save_devcontainer_config(devcontainer_path: str, devcontainer: Dict[str, Any]) -> None:
    """
    Save devcontainer configuration to JSON file.
    
    Args:
        devcontainer_path: Path to the devcontainer.json file
        devcontainer: Devcontainer configuration dictionary
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(devcontainer_path), exist_ok=True)
    
    # Write the updated configuration
    with open(devcontainer_path, 'w') as f:
        json.dump(devcontainer, f, indent=2)


def main():
    """Main entry point for the script."""
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    
    # Construct paths
    extensions_path = script_dir / EXTENSIONS_CONFIG
    devcontainer_path = script_dir / DEVCONTAINER_PATH
    
    print(f"Loading extensions configuration from {extensions_path}")
    extensions_config = load_extensions_config(extensions_path)
    
    # Get critical extensions
    critical_extensions = extensions_config.get('critical', [])
    if not critical_extensions:
        print("Warning: No critical extensions found in configuration")
    
    print(f"Loading devcontainer configuration from {devcontainer_path}")
    devcontainer = load_devcontainer_config(devcontainer_path)
    
    print(f"Updating devcontainer with {len(critical_extensions)} critical extensions")
    updated_devcontainer = update_devcontainer(devcontainer, critical_extensions)
    
    print(f"Saving updated devcontainer configuration to {devcontainer_path}")
    save_devcontainer_config(devcontainer_path, updated_devcontainer)
    
    print("Done!")


if __name__ == "__main__":
    main()