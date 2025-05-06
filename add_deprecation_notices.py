#!/usr/bin/env python3
"""
Add Deprecation Notices

This script adds deprecation notices to specified files that are planned
for removal in future releases. It preserves the original file content
while adding a clearly marked deprecation notice at the top.
"""

import os
import re
import argparse
from typing import List, Dict, Optional

# Mapping of files to their deprecation notices
DEPRECATED_FILES = {
    "updated_phidata_wrapper.py": {
        "notice": """
DEPRECATED: This file is deprecated and will be removed in a future release.

This older agent wrapper has been moved to the proper package structure and improved.
Please use the official implementation at packages/agents/src/phidata/wrapper.py instead,
which provides:
- Better integration with the agent registry
- Improved error handling
- Support for structured outputs
- Streaming response capabilities
- Better memory and storage integration

Example migration:
from updated_phidata_wrapper import PhidataAgentWrapper  # Old
# Change to:
from packages.agents.src.phidata.wrapper import PhidataAgentWrapper  # New
""",
    },
    "packages/shared/src/storage/firestore/firestore_memory.py": {
        "notice": """
DEPRECATED: This implementation is deprecated and will be removed in a future release.

Please use the FirestoreMemoryManagerV2 implementation at v2/adapter.py instead, which provides:
- Improved error handling and recovery
- Better type safety and validation
- Enhanced performance with optimized queries
- More robust health checks
- Better integration with monitoring systems

Example migration:
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
# Change to:
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
""",
    },
}

def add_deprecation_notice(file_path: str, notice: str) -> bool:
    """
    Add deprecation notice to a file.
    
    Args:
        file_path: Path to the file to modify
        notice: Deprecation notice to add
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if the file already has a deprecation notice
        if "DEPRECATED:" in content[:500]:
            print(f"[INFO] File {file_path} already has a deprecation notice")
            return False
        
        # Check if it's a Python file
        is_python = file_path.endswith('.py')
        
        if is_python:
            # Look for the docstring pattern
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                # Extract the docstring
                docstring = docstring_match.group(0)
                # Replace with docstring + deprecation notice
                new_docstring = f'"""{notice}\n{docstring[3:]}'
                new_content = content.replace(docstring, new_docstring, 1)
            else:
                # Add a new docstring with deprecation notice at the top
                new_content = f'"""{notice}\n"""\n\n{content}'
        else:
            # For non-Python files, just prepend the notice with a comment marker
            notice_with_comments = notice.replace("\n", "\n# ")
            new_content = f"# {notice_with_comments}\n\n{content}"
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        print(f"[SUCCESS] Added deprecation notice to {file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to add deprecation notice to {file_path}: {str(e)}")
        return False

def main():
    """Main function to add deprecation notices to files."""
    parser = argparse.ArgumentParser(description="Add deprecation notices to files")
    parser.add_argument('--dry-run', action='store_true', help='Print but do not modify files')
    parser.add_argument('--file', type=str, help='Process only this specific file')
    args = parser.parse_args()
    
    base_dir = "/workspaces/orchestra-main"
    
    for rel_file_path, config in DEPRECATED_FILES.items():
        # Skip if we're only processing a specific file
        if args.file and rel_file_path != args.file:
            continue
            
        file_path = os.path.join(base_dir, rel_file_path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            print(f"[WARNING] File not found: {file_path}")
            continue
            
        if args.dry_run:
            print(f"[DRY RUN] Would add deprecation notice to {file_path}")
        else:
            add_deprecation_notice(file_path, config["notice"])
    
    print("\nDeprecation notices have been added.")
    print("Next steps:")
    print("1. Verify the notices have been added correctly")
    print("2. Run tests to ensure no functionality is broken")
    print("3. Consider adding a specific removal timeline to the notices")

if __name__ == "__main__":
    main()
