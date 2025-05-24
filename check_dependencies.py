#!/usr/bin/env python3
"""
check_dependencies.py - Validate pip dependencies against requirements.txt.

- Ensures all packages in requirements.txt are installed in the active venv.
- Warns if any required packages are missing or have version mismatches.
- Optionally, lists outdated packages and suggests updates.

Usage:
    python check_dependencies.py [--show-outdated]
"""

import sys
import os
import subprocess
import pkg_resources

REQUIREMENTS_FILES = [
    "requirements.txt",
    "orchestrator/requirements.txt",
    "codespaces_pip_requirements.txt"
]

def find_requirements_file():
    for fname in REQUIREMENTS_FILES:
        if os.path.isfile(fname):
            return fname
    print("ERROR: No requirements.txt file found.")
    sys.exit(1)

def parse_requirements(req_file):
    with open(req_file, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [pkg_resources.Requirement.parse(line) for line in lines]

def check_installed(requirements):
    installed = {pkg.key: pkg for pkg in pkg_resources.working_set}
    missing = []
    mismatched = []
    for req in requirements:
        pkg = installed.get(req.key)
        if not pkg:
            missing.append(str(req))
        elif pkg not in req:
            mismatched.append(f"{pkg.project_name}=={pkg.version} (required: {req})")
    return missing, mismatched

def show_outdated():
    print("\nChecking for outdated packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"], check=False)
    except Exception as e:
        print(f"Failed to check outdated packages: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate pip dependencies against requirements.txt")
    parser.add_argument("--show-outdated", action="store_true", help="List outdated packages")
    args = parser.parse_args()

    req_file = find_requirements_file()
    print(f"Using requirements file: {req_file}")
    requirements = parse_requirements(req_file)
    missing, mismatched = check_installed(requirements)

    if missing:
        print("ERROR: Missing packages:")
        for pkg in missing:
            print(f"  - {pkg}")
    if mismatched:
        print("ERROR: Version mismatches:")
        for pkg in mismatched:
            print(f"  - {pkg}")

    if not missing and not mismatched:
        print("All required packages are installed and match requirements.txt.")
    else:
        sys.exit(1)

    if args.show_outdated:
        show_outdated()

if __name__ == "__main__":
    main()