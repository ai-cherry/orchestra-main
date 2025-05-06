#!/usr/bin/env python3
"""
Validate Poetry Lock File

This script validates that the Poetry lock file is in sync with the pyproject.toml file.
It checks for:
1. Lock file existence
2. Lock file freshness (in sync with pyproject.toml)
3. Dependency consistency

Usage:
    python scripts/validate_poetry_lock.py [--fix]

Options:
    --fix    Update the lock file if it's out of sync
"""

import argparse
import os
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


def check_poetry_installed():
    """Check if Poetry is installed."""
    try:
        subprocess.run(
            ["poetry", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_lock_file_exists():
    """Check if poetry.lock file exists."""
    lock_file = Path("poetry.lock")
    return lock_file.exists()


def check_lock_file_fresh():
    """Check if poetry.lock is in sync with pyproject.toml."""
    try:
        result = subprocess.run(
            ["poetry", "check", "--lock"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def update_lock_file():
    """Update the poetry.lock file."""
    try:
        subprocess.run(
            ["poetry", "lock", "--no-update"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.SubprocessError:
        return False


def check_dependency_consistency():
    """Check for dependency consistency issues."""
    try:
        result = subprocess.run(
            ["poetry", "check"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0, result.stderr
    except subprocess.SubprocessError:
        return False, "Failed to run poetry check"


def get_dependency_info():
    """Get information about dependencies."""
    try:
        result = subprocess.run(
            ["poetry", "show", "--tree"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except subprocess.SubprocessError:
        return "Failed to get dependency information"


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate Poetry lock file")
    parser.add_argument(
        "--fix", action="store_true", help="Update the lock file if it's out of sync"
    )
    args = parser.parse_args()

    # Check if Poetry is installed
    if not check_poetry_installed():
        print("❌ Poetry is not installed or not in PATH")
        print("   Please install Poetry: https://python-poetry.org/docs/#installation")
        return 1

    # Check if lock file exists
    if not check_lock_file_exists():
        print("❌ poetry.lock file not found")
        if args.fix:
            print("   Generating lock file...")
            if update_lock_file():
                print("✅ Lock file generated successfully")
            else:
                print("❌ Failed to generate lock file")
                return 1
        else:
            print("   Run 'poetry lock' to generate the lock file")
            print("   Or run this script with --fix to automatically generate it")
            return 1
    else:
        print("✅ poetry.lock file exists")

    # Check if lock file is fresh
    if not check_lock_file_fresh():
        print("❌ poetry.lock is out of sync with pyproject.toml")
        if args.fix:
            print("   Updating lock file...")
            if update_lock_file():
                print("✅ Lock file updated successfully")
            else:
                print("❌ Failed to update lock file")
                return 1
        else:
            print("   Run 'poetry lock --no-update' to update the lock file")
            print("   Or run this script with --fix to automatically update it")
            return 1
    else:
        print("✅ poetry.lock is in sync with pyproject.toml")

    # Check for dependency consistency
    consistent, error_message = check_dependency_consistency()
    if not consistent:
        print("❌ Dependency consistency issues found:")
        print(error_message)
        return 1
    else:
        print("✅ No dependency consistency issues found")

    # Print dependency information
    print("\n📦 Dependency Information:")
    print(get_dependency_info())

    print("\n✅ All checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())