#!/usr/bin/env python3
"""
Script to check for missing deprecation notices in legacy files.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Legacy file patterns that should have deprecation notices
LEGACY_FILE_PATTERNS = [
    # Main legacy files
    r"future/.*\.py$",
    r"updated_phidata_wrapper\.py$",
    # Legacy setup scripts
    r"setup_.*_legacy\.py$",
    r".*_setup_old\.py$",
    r".*_deprecated\.py$",
    # Add more patterns here as needed
]

# Regex pattern for deprecation notice
DEPRECATION_REGEX = r'("""[\s]*DEPRECATED|# DEPRECATED|\*\*\* DEPRECATED|DEPRECATED:)'

def find_files(base_dir: str, patterns: List[str]) -> Set[Path]:
    """Find files matching the provided patterns."""
    matching_files = set()
    for root, _, files in os.walk(base_dir):
        # Skip .git, google-cloud-sdk, virtual environments
        if any(skip in root for skip in [".git", "google-cloud-sdk", ".venv", "__pycache__"]):
            continue
            
        for file in files:
            filepath = Path(os.path.join(root, file))
            rel_path = filepath.relative_to(base_dir)
            for pattern in patterns:
                if re.search(pattern, str(rel_path)):
                    matching_files.add(filepath)
    return matching_files

def check_deprecation_notice(file_path: Path) -> bool:
    """Check if the file has a deprecation notice at the top."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first 30 lines to check for deprecation notice
            header = ''.join(f.readline() for _ in range(30))
            if re.search(DEPRECATION_REGEX, header, re.IGNORECASE):
                return True
            return False
    except UnicodeDecodeError:
        # Skip binary files
        return True

def create_deprecation_notice(file_path: Path) -> str:
    """Create an appropriate deprecation notice for the file."""
    # Determine file type from extension
    ext = file_path.suffix
    
    # Extract base name without extension
    base_name = file_path.stem
    
    # Base deprecation notice
    if ext == ".py":
        notice = f'''"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This legacy file has been replaced by a newer implementation with improved architecture 
and error handling. Please consult the project documentation for the recommended 
replacement module.

Example migration:
from {file_path.stem} import * # Old
# Change to:
# Import the appropriate replacement module
"""

'''
    elif ext == ".sh":
        notice = '''#!/bin/bash
# DEPRECATED: This script is deprecated and will be removed in a future release.
# Please refer to the project documentation for the recommended replacement script.

'''
    else:
        notice = '''# DEPRECATED: This file is deprecated and will be removed in a future release.
# Please refer to the project documentation for the recommended replacement.

'''
    return notice

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check legacy files for deprecation notices")
    parser.add_argument("--base-dir", type=str, default=".", help="Base directory to search")
    parser.add_argument("--fix", action="store_true", help="Add deprecation notices to files missing them")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    args = parser.parse_args()
    
    # Find legacy files
    print(f"Searching for legacy files in {args.base_dir}...")
    legacy_files = find_files(args.base_dir, LEGACY_FILE_PATTERNS)
    print(f"Found {len(legacy_files)} potential legacy files")
    
    # Check deprecation notices
    missing_notices = []
    has_notices = []
    
    for file_path in legacy_files:
        if args.verbose:
            print(f"Checking {file_path}...")
            
        if check_deprecation_notice(file_path):
            has_notices.append(file_path)
        else:
            missing_notices.append(file_path)
    
    # Report results
    print(f"\n{len(has_notices)} files have deprecation notices")
    if args.verbose and has_notices:
        for file_path in has_notices:
            print(f"✓ {file_path}")
    
    print(f"\n{len(missing_notices)} files are missing deprecation notices")
    for file_path in missing_notices:
        print(f"✗ {file_path}")
    
    # Fix files if requested
    if args.fix and missing_notices:
        print("\nAdding deprecation notices to files:")
        for file_path in missing_notices:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create appropriate deprecation notice
                notice = create_deprecation_notice(file_path)
                
                # Write content with deprecation notice
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(notice + content)
                
                print(f"✓ Added deprecation notice to {file_path}")
            except Exception as e:
                print(f"✗ Failed to add deprecation notice to {file_path}: {e}")
    
    # Exit with error code if missing notices
    if missing_notices:
        if not args.fix:
            print("\nRun with --fix to add deprecation notices to these files")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
