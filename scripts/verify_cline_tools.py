#!/usr/bin/env python3
"""
Cline MCP Tool Version Verifier

This script checks if the required Cline MCP tools are installed and have the correct versions.
"""

import subprocess
import sys
import re
import json
import argparse
import os
from pathlib import Path

def run_command(command):
    """Run a command and return its output"""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            shell=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"stderr: {e.stderr}")
        return None

def check_cline_installed():
    """Check if Cline MCP is installed"""
    result = run_command("which cline 2>/dev/null || echo 'not found'")
    if result and result != 'not found':
        print(f"✅ Cline MCP is installed at: {result}")
        return True
    else:
        print("❌ Cline MCP is not installed")
        return False

def get_tool_version(tool_name):
    """Get the version of a Cline MCP tool"""
    # First try with --json flag which might be supported in newer versions
    result = run_command(f"cline tool info {tool_name} --json 2>/dev/null || echo 'fallback'")
    
    if result and result != 'fallback':
        try:
            info = json.loads(result)
            return info.get("version")
        except json.JSONDecodeError:
            pass  # Fall through to regex method
    
    # Try the regular output format
    result = run_command(f"cline tool info {tool_name} 2>/dev/null || echo 'not installed'")
    if result == 'not installed':
        return None
        
    # Try regex if JSON parsing fails
    match = re.search(r'version:\s*([0-9.]+)', result)
    if match:
        return match.group(1)
    
    # Look for version in any format
    match = re.search(r'([0-9]+\.[0-9]+\.[0-9]+)', result)
    if match:
        return match.group(1)
    
    return None

def check_version_requirement(version, required_version):
    """Check if a version meets the minimum requirement"""
    if not version:
        return False
    
    # Convert versions to tuples of integers
    try:
        v1 = tuple(map(int, version.split('.')))
        v2 = tuple(map(int, required_version.split('.')))
    except ValueError:
        print(f"⚠️ Could not parse version '{version}' or '{required_version}'")
        return False
    
    # Pad shorter tuple with zeros
    if len(v1) < len(v2):
        v1 = v1 + (0,) * (len(v2) - len(v1))
    elif len(v2) < len(v1):
        v2 = v2 + (0,) * (len(v1) - len(v2))
    
    return v1 >= v2

def verify_tool_versions(required_tools=None):
    """Verify the versions of required Cline MCP tools"""
    if required_tools is None:
        required_tools = [
            ('figma-sync', '1.3.0'),
            ('terraform-linter', '2.8.0'),
            ('gcp-cost', '0.9.0')
        ]
    
    all_passed = True
    missing_tools = []
    outdated_tools = []
    
    if not check_cline_installed():
        print("❌ Cannot verify tool versions without Cline MCP installed")
        print("\nInstallation instructions:")
        print("  1. Run: curl -sSL https://install.cline.dev | sh")
        print("  2. Add Cline to your PATH: source ~/.cline/env")
        return False
    
    for tool_name, required_version in required_tools:
        version = get_tool_version(tool_name)
        
        if not version:
            print(f"❌ {tool_name} is not installed")
            missing_tools.append((tool_name, required_version))
            all_passed = False
            continue
        
        if check_version_requirement(version, required_version):
            print(f"✅ {tool_name} version {version} meets requirement (>= {required_version})")
        else:
            print(f"❌ {tool_name} version {version} does not meet requirement (>= {required_version})")
            outdated_tools.append((tool_name, version, required_version))
            all_passed = False
    
    return all_passed, missing_tools, outdated_tools

def print_installation_instructions(missing_tools, outdated_tools):
    """Print installation instructions for missing or outdated tools"""
    if missing_tools or outdated_tools:
        print("\n=== INSTALLATION INSTRUCTIONS ===")
        
        if missing_tools:
            print("\nMissing tools:")
            for tool_name, required_version in missing_tools:
                print(f"  cline install {tool_name} --min-version {required_version}")
        
        if outdated_tools:
            print("\nOutdated tools:")
            for tool_name, current_version, required_version in outdated_tools:
                print(f"  cline update {tool_name} --min-version {required_version} # currently {current_version}")

def create_tool_configuration(config_file_path):
    """Create a default tool configuration file"""
    default_config = {
        "tools": [
            {"name": "figma-sync", "min_version": "1.3.0"},
            {"name": "terraform-linter", "min_version": "2.8.0"},
            {"name": "gcp-cost", "min_version": "0.9.0"}
        ]
    }
    
    config_dir = os.path.dirname(config_file_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    with open(config_file_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✅ Created configuration file at {config_file_path}")
    return default_config

def load_tool_configuration(config_file_path):
    """Load tool configuration from file"""
    if not os.path.exists(config_file_path):
        print(f"⚠️ Configuration file {config_file_path} not found, creating default")
        return create_tool_configuration(config_file_path)
    
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        
        # Validate configuration format
        if not isinstance(config, dict) or "tools" not in config:
            print(f"⚠️ Invalid configuration format in {config_file_path}, using default")
            return create_tool_configuration(config_file_path)
        
        return config
    except json.JSONDecodeError:
        print(f"⚠️ Invalid JSON in {config_file_path}, using default")
        return create_tool_configuration(config_file_path)

def main():
    parser = argparse.ArgumentParser(description='Verify Cline MCP tool versions')
    parser.add_argument('--config', default='config/cline_tools.json',
                      help='Path to tool configuration file')
    parser.add_argument('--create-config', action='store_true',
                      help='Create a default configuration file')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_tool_configuration(args.config)
        return 0
    
    config = load_tool_configuration(args.config)
    required_tools = [(tool["name"], tool["min_version"]) for tool in config["tools"]]
    
    print("Verifying Cline MCP tool versions...")
    for tool_name, required_version in required_tools:
        print(f"• {tool_name} (>= {required_version})")
    
    result, missing_tools, outdated_tools = verify_tool_versions(required_tools)
    
    if result:
        print("\n✅ All Cline MCP tools meet version requirements")
    else:
        print("\n❌ Some Cline MCP tools are missing or don't meet version requirements")
        print_installation_instructions(missing_tools, outdated_tools)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
