#!/usr/bin/env python3
"""
Fix Python version references across the entire project.
This script will update all references from Python 3.11 to Python 3.10.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Files to update with their specific patterns
FILE_UPDATES = {
    # Pre-commit config - the main culprit!
    ".pre-commit-config.yaml": [
        (
            r"# Enforces Python 3\.11\+ and Poetry.*",
            "# Enforces Python 3.10+ and Poetry for all pre-commit hooks.",
        ),
        (
            r"# All hooks use python3\.11.*",
            "# All hooks use python3.10 and run in the Poetry-managed environment.",
        ),
        (r"language_version: python3\.11", "language_version: python3.10"),
        (
            r"name: Validate Python 3\.11\+.*",
            "name: Validate Python 3.10+ and Poetry environment",
        ),
    ],
    # Scripts that check Python version
    "scripts/validate_python_env.sh": [
        (
            r"# Enforces Python 3\.11\+.*",
            "# Enforces Python 3.10+ and Poetry for all environments (local, CI, Docker).",
        ),
        (r'REQUIRED_PYTHON="3\.11"', 'REQUIRED_PYTHON="3.10"'),
        (
            r"ERROR: Python 3\.11\+ is required.*",
            "ERROR: Python 3.10+ is required. Detected: $PYTHON_VERSION",
        ),
    ],
    "scripts/review_ai_context.py": [
        (r'"Python 3\.11"', '"Python 3.10"'),
        (r"Python 3\.11\+ required", "Python 3.10+ required"),
        (r"upgrade to Python 3\.11 or later", "upgrade to Python 3.10 or later"),
    ],
    # GitHub workflows
    ".github/workflows/ci.yml": [
        (r"Python 3\.11\+ required", "Python 3.10+ required"),
        (r"Set up Python 3\.11", "Set up Python 3.10"),
        (r'python-version: "3\.11"', 'python-version: "3.10"'),
    ],
    ".github/workflows/ci-cd.yml": [
        (r'python-version: "3\.11"', 'python-version: "3.10"'),
    ],
    # Dockerfiles
    "Dockerfile": [
        (r"FROM python:3\.11-slim-bullseye", "FROM python:3.10-slim-bullseye"),
    ],
    "Dockerfile.webscraping": [
        (r"FROM python:3\.11-slim-bullseye", "FROM python:3.10-slim-bullseye"),
    ],
    # mypy config
    "mypy.ini": [
        (r"python_version = 3\.11", "python_version = 3.10"),
    ],
    # Cloud build
    "cloudbuild.yaml": [
        (r'name: "python:3\.11"', 'name: "python:3.10"'),
    ],
    # Scan script
    "scan_github_workflows.py": [
        (r'if python_version != "3\.11":', 'if python_version != "3.10":'),
        (r"instead of 3\.11 in step", "instead of 3.10 in step"),
        (r'"Update to Python 3\.11"', '"Update to Python 3.10"'),
    ],
}

# Patterns to replace in all other files
GENERAL_PATTERNS = [
    # Version specifications
    (r"Python 3\.11\+", "Python 3.10+"),
    (r"python:3\.11", "python:3.10"),
    (r"python3\.11", "python3.10"),
    (r'python-version: ["\']3\.11["\']', 'python-version: "3.10"'),
    (r"Python version 3\.11", "Python version 3.10"),
    (r"Python 3\.11 or higher", "Python 3.10 or higher"),
    (r"Python 3\.11 or later", "Python 3.10 or later"),
    (r"Python 3\.11,", "Python 3.10,"),
    (r"version 3\.11", "version 3.10"),
    (r"3\.11\+ required", "3.10+ required"),
    (r"3\.11\+ REQUIRED", "3.10+ REQUIRED"),
    (r"3\.11\+ only", "3.10+ only"),
    (r"3\.11\+ features", "3.10+ features"),
    (r"Target Python 3\.11\+", "Target Python 3.10+"),
    (r"Python 3\.11\+ everywhere", "Python 3.10+ everywhere"),
    (r"Python 3\.11\+ and Poetry", "Python 3.10+ and Poetry"),
    (r"Python 3\.11\+ and Node", "Python 3.10+ and Node"),
    (r"Python 3\.11\+ is required", "Python 3.10+ is required"),
    (r"Python 3\.11\+ style", "Python 3.10+ style"),
    (r"Python 3\.11-slim", "Python 3.10-slim"),
    (r"python:3\.11-slim-bullseye", "python:3.10-slim-bullseye"),
    (r"python:3\.11-bookworm", "python:3.10-bookworm"),
    (r"devcontainers/python:3\.11", "devcontainers/python:3.10"),
    (
        r"Programming Language :: Python :: 3\.11",
        "Programming Language :: Python :: 3.10",
    ),
    (r"Python Version Standardized to 3\.11", "Python Version Standardized to 3.10"),
    (r"All files now use Python 3\.11", "All files now use Python 3.10"),
    (r"Uses Python 3\.11 and Poetry", "Uses Python 3.10 and Poetry"),
    (r"Python 3\.11\+ virtual environment", "Python 3.10+ virtual environment"),
    (r"python3\.11 -m venv", "python3.10 -m venv"),
    (r"Should be 3\.11\+", "Should be 3.10+"),
    (r"Python 3\.11 dependency", "Python 3.10 dependency"),
    (r"Python 3\.11\.", "Python 3.10."),
    (r"Python 3\.11\.x", "Python 3.10.x"),
    (r"Python 3\.11\.6", "Python 3.10.12"),
    (r"Python 3\.11\.4", "Python 3.10.12"),
    (r'PYTHON_VERSION: "3\.11"', 'PYTHON_VERSION: "3.10"'),
    (r'PYTHON_VERSION="3\.11"', 'PYTHON_VERSION="3.10"'),
]

# Files to skip
SKIP_FILES = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    "fix_python_version_forever.py",  # Don't modify this script
    ".python-version-lock",  # Already fixed
    "pyproject.toml",  # Already fixed
    ".tool-versions",  # Already fixed
    "README.md",  # Already fixed
    "scripts/config_validator.py",  # Already fixed
    "scripts/check_venv.py",  # Already fixed
}


def should_process_file(filepath: str) -> bool:
    """Check if file should be processed."""
    path = Path(filepath)

    # Skip if in skip list
    for skip in SKIP_FILES:
        if skip in str(path):
            return False

    # Skip binary files
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(1)
        return True
    except:
        return False


def update_file(filepath: str, patterns: List[Tuple[str, str]]) -> bool:
    """Update a file with the given patterns."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main() -> None:
    """Main function to fix all Python version references."""
    print("🔧 Fixing Python version references across the entire project...")
    print("=" * 60)

    updated_files = []

    # First, update specific files with custom patterns
    print("\n📝 Updating specific configuration files...")
    for filepath, patterns in FILE_UPDATES.items():
        if os.path.exists(filepath):
            if update_file(filepath, patterns):
                updated_files.append(filepath)
                print(f"✅ Updated: {filepath}")
            else:
                print(f"⏭️  No changes needed: {filepath}")
        else:
            print(f"⚠️  File not found: {filepath}")

    # Then, update all other files with general patterns
    print("\n🔍 Scanning all other files...")
    for root, dirs, files in os.walk("."):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_FILES]

        for file in files:
            filepath = os.path.join(root, file)

            # Skip if already processed or should skip
            if filepath in FILE_UPDATES or not should_process_file(filepath):
                continue

            if update_file(filepath, GENERAL_PATTERNS):
                updated_files.append(filepath)
                print(f"✅ Updated: {filepath}")

    print("\n" + "=" * 60)
    print(f"✨ Updated {len(updated_files)} files!")

    if updated_files:
        print("\n📋 Files updated:")
        for f in sorted(updated_files):
            print(f"  - {f}")

    print("\n🎉 Python version standardization complete!")
    print("All references have been updated from Python 3.11 to Python 3.10")

    # Special note about pre-commit
    if ".pre-commit-config.yaml" in updated_files:
        print("\n⚠️  IMPORTANT: Pre-commit hooks have been updated!")
        print("Run these commands to reinstall the hooks:")
        print("  pre-commit uninstall")
        print("  pre-commit install")


if __name__ == "__main__":
    main()
