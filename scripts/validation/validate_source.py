#!/usr/bin/env python3
# validate_source.py - Validates source code accessibility

import os
import sys
import argparse
import subprocess
from pathlib import Path


def validate_file_structure():
    """Validate critical directories and files exist"""
    critical_dirs = [
        "agent",
        "core",
        "packages",
        "scripts",
        "templates",
        "infra",
        "docs",
        "apps",
    ]

    critical_files = ["cloudbuild.yaml", "pyproject.toml", ".flake8", "Dockerfile"]

    results = {"dirs": {}, "files": {}}

    for directory in critical_dirs:
        exists = os.path.isdir(directory)
        results["dirs"][directory] = exists

    for file in critical_files:
        exists = os.path.isfile(file)
        results["files"][file] = exists

    return results


def validate_git_access():
    """Verify git repository is properly configured"""
    try:
        result = subprocess.run(["git", "status"], capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)


def validate_python_env():
    """Check Python environment and dependencies"""
    try:
        # Check poetry installation
        poetry_result = subprocess.run(
            ["poetry", "--version"], capture_output=True, text=True
        )

        # Check ability to install dependencies
        install_result = subprocess.run(
            ["poetry", "check"], capture_output=True, text=True
        )

        return (
            True,
            f"Poetry: {poetry_result.stdout.strip()}\nCheck: {install_result.stdout.strip()}",
        )
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Validate source code accessibility")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()

    print("### File Structure Verification")
    structure = validate_file_structure()

    print("#### Critical Directories:")
    for dir_name, exists in structure["dirs"].items():
        status = "✅" if exists else "❌"
        print(f"* {dir_name}: {status}")

    print("\n#### Critical Files:")
    for file_name, exists in structure["files"].items():
        status = "✅" if exists else "❌"
        print(f"* {file_name}: {status}")

    print("\n### Git Repository Verification")
    git_ok, git_output = validate_git_access()
    status = "✅" if git_ok else "❌"
    print(f"* Git repository accessible: {status}")

    print("\n### Python Environment Verification")
    py_ok, py_output = validate_python_env()
    status = "✅" if py_ok else "❌"
    print(f"* Python/Poetry environment: {status}")
    print(f"```\n{py_output}\n```")

    # Overall status
    all_ok = (
        all(structure["dirs"].values())
        and all(structure["files"].values())
        and git_ok
        and py_ok
    )
    print(f"\n### Overall Source Code Accessibility: {'✅' if all_ok else '❌'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
