#!/usr/bin/env python3
"""
Fix for pre-commit hook configuration.

This script updates the pre-commit hook configuration to properly handle
the analyze_code_wrapper.py script.
"""

import os
import sys
from pathlib import Path


def update_pre_commit_hook():
    """Update the pre-commit hook to properly handle files."""
    hook_path = Path(".git/hooks/pre-commit")

    # Check if hook exists
    if not hook_path.exists():
        print("Pre-commit hook not found. Creating a new one.")

        # Create a new hook
        hook_content = """#!/bin/bash
set -e

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\\.py$')

if [ -n "$STAGED_FILES" ]; then
    echo "Running Gemini code analysis on staged Python files..."
    python /workspaces/orchestra-main/analyze_code_wrapper.py $STAGED_FILES
fi
"""
        # Write the hook
        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make it executable
        os.chmod(hook_path, 0o755)
        print(f"Created new pre-commit hook at {hook_path}")
        return True

    # Read the existing hook
    with open(hook_path, "r") as f:
        content = f.read()

    # Check if it's already using the correct format
    if "analyze_code_wrapper.py $STAGED_FILES" in content:
        print("Pre-commit hook already configured correctly.")
        return True

    # Update the hook
    updated_content = content.replace(
        "python /workspaces/orchestra-main/analyze_code_wrapper.py",
        "python /workspaces/orchestra-main/analyze_code_wrapper.py $STAGED_FILES"
    )

    # If no replacement was made, the hook might be using a different pattern
    if updated_content == content:
        print("Could not update the pre-commit hook automatically.")
        print("Please check the hook manually and update it to pass files as arguments.")
        return False

    # Write the updated hook
    with open(hook_path, "w") as f:
        f.write(updated_content)

    # Make sure it's executable
    os.chmod(hook_path, 0o755)

    print(f"Updated pre-commit hook at {hook_path}")
    return True


if __name__ == "__main__":
    if update_pre_commit_hook():
        print("Pre-commit hook update successful!")
        sys.exit(0)
    else:
        print("Pre-commit hook update failed.")
        sys.exit(1)
