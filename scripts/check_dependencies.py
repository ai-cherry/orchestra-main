import argparse
import subprocess
import sys

import pkg_resources

DEFAULT_REQUIREMENTS_FILE = "requirements.txt"


def get_installed_packages():
    """Returns a dictionary of installed packages and their versions."""
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    return installed_packages


def get_required_packages(requirements_file: str):
    """Parses a requirements file and returns a dictionary of required packages and versions."""
    required = {}
    try:
        with open(requirements_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-r"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        required[name.strip().lower()] = version.strip()
                    elif "~=" in line or ">=" in line or "<" in line:
                        # For now, just record the name for range dependencies
                        # More sophisticated parsing could be added here
                        name = line.split("~", 1)[0].split(">", 1)[0].split("<", 1)[0].strip()
                        required[name.strip().lower()] = None  # Indicates ranged/unpinned
                    else:
                        required[line.strip().lower()] = None  # Unpinned
    except FileNotFoundError:
        print(f"ERROR: Requirements file not found: {requirements_file}")
        sys.exit(1)
    return required


def check_dependencies(requirements_file: str, show_outdated: bool = False):
    """Checks if all required packages are installed and optionally shows outdated packages."""
    print(f"Checking dependencies from: {requirements_file}")
    installed = get_installed_packages()
    required = get_required_packages(requirements_file)
    missing_packages = []
    mismatched_versions = []

    for req_name, req_version in required.items():
        if req_name not in installed:
            missing_packages.append(f"{req_name}{ '==' + req_version if req_version else ''}")
        elif req_version and installed[req_name] != req_version:
            mismatched_versions.append(f"{req_name} (required: {req_version}, installed: {installed[req_name]})")

    if missing_packages:
        print("\nERROR: Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")

    if mismatched_versions:
        print("\nERROR: Mismatched package versions:")
        for pkg in mismatched_versions:
            print(f"  - {pkg}")

    if not missing_packages and not mismatched_versions:
        print("All required dependencies are installed and versions match.")
    else:
        print("\nPlease run 'make install' or 'pip install -r requirements.txt' to fix.")
        sys.exit(1)

    if show_outdated:
        print("\nChecking for outdated packages...")
        try:
            # Use pip list --outdated. Ensure it runs in the current venv context.
            # The `sys.executable` ensures pip from the current venv is used.
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated"], capture_output=True, text=True, check=False
            )
            if result.stdout:
                print("Outdated packages found:")
                print(result.stdout)
            else:
                print("No outdated packages found.")
            if result.stderr:
                print(f"Error checking outdated packages: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Could not check for outdated packages: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Python dependencies.")
    parser.add_argument(
        "--file",
        default=DEFAULT_REQUIREMENTS_FILE,
        help=f"Path to the requirements file (default: {DEFAULT_REQUIREMENTS_FILE})",
    )
    parser.add_argument(
        "--show-outdated", action="store_true", help="Show outdated packages using pip list --outdated."
    )
    args = parser.parse_args()
    check_dependencies(args.file, args.show_outdated)
