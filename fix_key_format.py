#!/usr/bin/env python3
"""
fix_key_format.py - Fix common formatting issues in GCP service account key files

This script checks for and fixes common formatting issues in GCP service account key files:
1. Escaped newlines in the private key
2. Missing or extra characters
3. Incorrect JSON formatting

Usage:
  python fix_key_format.py --input credentials.json --output fixed_credentials.json
"""

import json
import argparse
import re
import sys
from typing import Dict, Any, Optional

def load_key_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a service account key file and return the parsed JSON."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to parse as JSON
        try:
            key_data = json.loads(content)
            return key_data
        except json.JSONDecodeError as e:
            print(f"Error: Key file is not valid JSON: {e}")
            return None
    except FileNotFoundError:
        print(f"Error: Key file not found: {file_path}")
        return None

def fix_private_key(private_key: str) -> str:
    """Fix common issues with private key formatting."""
    # Check if the key has escaped newlines
    if '\\n' in private_key and '\n' not in private_key:
        print("Fixing: Replacing escaped newlines (\\n) with actual newlines")
        private_key = private_key.replace('\\n', '\n')
    
    # Ensure the key starts and ends correctly
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("Warning: Private key does not start with '-----BEGIN PRIVATE KEY-----'")
    
    if not private_key.endswith('-----END PRIVATE KEY-----\n') and not private_key.endswith('-----END PRIVATE KEY-----'):
        print("Warning: Private key does not end with '-----END PRIVATE KEY-----'")
    
    # Ensure there's a newline after BEGIN and before END
    private_key = re.sub(r'(-----BEGIN PRIVATE KEY-----)([^\n])', r'\1\n\2', private_key)
    private_key = re.sub(r'([^\n])(-----END PRIVATE KEY-----)', r'\1\n\2', private_key)
    
    # Ensure there's a newline at the end
    if not private_key.endswith('\n'):
        private_key += '\n'
    
    return private_key

def check_and_fix_key(key_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check and fix common issues with a service account key."""
    fixed_key = key_data.copy()
    
    # Check for required fields
    required_fields = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri',
        'auth_provider_x509_cert_url', 'client_x509_cert_url'
    ]
    
    for field in required_fields:
        if field not in key_data:
            print(f"Error: Key file is missing required field: {field}")
            if field == 'type':
                print("Adding default value: 'service_account'")
                fixed_key['type'] = 'service_account'
    
    # Fix private key if present
    if 'private_key' in fixed_key:
        fixed_key['private_key'] = fix_private_key(fixed_key['private_key'])
    
    return fixed_key

def save_key_file(key_data: Dict[str, Any], file_path: str) -> bool:
    """Save a service account key to a file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(key_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving key file: {e}")
        return False

def main():
    """Main function."""
    
    parser = argparse.ArgumentParser(description='Fix common formatting issues in GCP service account key files')
    parser.add_argument('--input', default='credentials.json', help='Path to the input service account key file')
    parser.add_argument('--output', default='fixed_credentials.json', help='Path to save the fixed service account key file')
    parser.add_argument('--check-only', action='store_true', help='Only check for issues, do not fix')
    args = parser.parse_args()
    
    print(f"Checking service account key: {args.input}")
    
    # Load the key file
    key_data = load_key_file(args.input)
    if key_data is None:
        sys.exit(1)
    
    # Check the key type
    if key_data.get('type') != 'service_account':
        print(f"Warning: Key type is not 'service_account': {key_data.get('type')}")
    
    # Check and fix the key
    fixed_key = check_and_fix_key(key_data)
    
    # Check if any changes were made
    if fixed_key == key_data:
        print("No issues found in the key file.")
        sys.exit(0)
    
    # Save the fixed key
    if not args.check_only:
        print(f"Saving fixed key to: {args.output}")
        if save_key_file(fixed_key, args.output):
            print("Key file fixed successfully.")
            print(f"Use the fixed key file with: gcloud auth activate-service-account --key-file={args.output}")
        else:
            print("Failed to save fixed key file.")
            sys.exit(1)
    else:
        print("Issues found in the key file. Run without --check-only to fix them.")

if __name__ == "__main__":
    main()