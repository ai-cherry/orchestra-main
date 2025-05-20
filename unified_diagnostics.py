#!/usr/bin/env python3
"""
Orchestra Unified Diagnostics

This script performs a comprehensive health check of the Orchestra environment,
verifying the setup and configuration of all components.
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("diagnostics.log")],
)
logger = logging.getLogger("orchestra-diagnostics")

# ANSI colors for terminal output


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}==== {text} ===={Colors.END}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def run_command(command: str, check: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        return exit_code, stdout, stderr
    except Exception as e:
        logger.error(f"Failed to run command: {command}", exc_info=True)
        if check:
            print_error(f"Command failed: {command}")
            print_error(f"Error: {str(e)}")
        return 1, "", str(e)


def check_file_exists(path: str) -> bool:
    """Check if a file exists."""
    return os.path.isfile(path)


def check_dir_exists(path: str) -> bool:
    """Check if a directory exists."""
    return os.path.isdir(path)


def check_environment():
    """Check environment variables and basic system configuration."""
    print_header("Environment Check")

    # Check environment variables
    env_vars = {
        "GCP_PROJECT_ID": os.environ.get("GCP_PROJECT_ID"),
        "GCP_SA_KEY_PATH": os.environ.get("GCP_SA_KEY_PATH"),
        "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ),
        "FIGMA_PAT": os.environ.get("FIGMA_PAT"),
    }

    missing_vars = []
    for name, value in env_vars.items():
        if name == "FIGMA_PAT" and value:
            print_success(f"{name} is set")
        elif value:
            print_success(f"{name} is set to: {value}")
        else:
            print_warning(f"{name} is not set")
            missing_vars.append(name)

    if missing_vars:
        print_warning(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Run source setup_gcp_auth.sh to set these variables.")
    else:
        print_success("All required environment variables are set")


def check_gcp_auth():
    """Check GCP authentication status."""
    print_header("GCP Authentication")

    # Check service account key file
    key_path = os.environ.get("GCP_SA_KEY_PATH", "/tmp/vertex-agent-key.json")
    if check_file_exists(key_path):
        print_success(f"Service account key file found at {key_path}")

        # Try to verify key content
        exit_code, stdout, stderr = run_command(
            f"cat {key_path} | grep -q 'private_key'", check=False
        )
        if exit_code == 0:
            print_success("Service account key appears to be valid")
        else:
            print_warning(
                "Service account key may be invalid (couldn't find private_key)"
            )
    else:
        print_error(f"Service account key file not found at {key_path}")
        print("Run ./setup_gcp_auth.sh to create a new service account key.")

    # Check gcloud CLI configuration
    exit_code, stdout, stderr = run_command(
        "gcloud config get-value project", check=False
    )
    if exit_code == 0 and stdout.strip():
        project = stdout.strip()
        expected_project = os.environ.get("GCP_PROJECT_ID", "cherry-ai-project")

        if project == expected_project:
            print_success(f"gcloud configured with correct project: {project}")
        else:
            print_warning(
                f"gcloud configured with project {project}, expected {expected_project}"
            )
    else:
        print_error("Failed to get gcloud project configuration")

    # Try a simple API call
    exit_code, stdout, stderr = run_command(
        "python -c \"from google.cloud import storage; print('Connected to GCP:', storage.Client().project)\"",
        check=False,
    )

    if exit_code == 0:
        print_success("Successfully connected to GCP Storage API")
        print(f"  {stdout.strip()}")
    else:
        print_error("Failed to connect to GCP Storage API")
        print(f"  Error: {stderr.strip()}")
        print(
            "This may indicate an issue with your service account key or permissions."
        )


def check_terraform():
    """Check Terraform configuration."""
    print_header("Terraform Configuration")

    terraform_dir = "infra/orchestra-terraform"

    if not check_dir_exists(terraform_dir):
        print_error(f"Terraform directory not found at {terraform_dir}")
        return

    print_success(f"Terraform directory found at {terraform_dir}")

    # Check required files
    for file in ["main.tf", "variables.tf", "terraform.tfvars"]:
        if check_file_exists(f"{terraform_dir}/{file}"):
            print_success(f"Found {file}")
        else:
            print_error(f"Missing {file}")

    # Check if terraform is installed
    exit_code, stdout, stderr = run_command("terraform --version", check=False)
    if exit_code == 0:
        first_line_of_stdout = stdout.split("\n")[0]
        print_success(f"Terraform installed: {first_line_of_stdout}")
    else:
        print_error("Terraform not installed")
        return

    # Check terraform initialization
    exit_code, stdout, stderr = run_command(
        f"cd {terraform_dir} && terraform show", check=False
    )
    if exit_code == 0:
        print_success("Terraform is initialized")
    else:
        print_warning("Terraform not initialized")
        print("Run 'cd infra/orchestra-terraform && terraform init' to initialize.")


def check_figma():
    """Check Figma integration."""
    print_header("Figma Integration")

    # Check Figma PAT
    figma_pat = os.environ.get("FIGMA_PAT")
    if not figma_pat:
        print_error("FIGMA_PAT environment variable not set")
        return

    print_success("FIGMA_PAT environment variable is set")

    # Check Figma sync script
    figma_script = "scripts/figma_gcp_sync.py"
    if check_file_exists(figma_script):
        print_success(f"Figma sync script found at {figma_script}")
    else:
        print_error(f"Figma sync script not found at {figma_script}")
        return

    # Check required Python packages for Figma integration
    packages = ["requests", "google.cloud.secretmanager", "google.cloud.aiplatform"]
    missing_packages = []

    for package in packages:
        exit_code, stdout, stderr = run_command(
            f"python -c 'import {package.split('.')[0]}'", check=False
        )
        if exit_code == 0:
            print_success(f"Python package '{package.split('.')[0]}' is installed")
        else:
            print_warning(f"Python package '{package.split('.')[0]}' is not installed")
            missing_packages.append(package.split(".")[0])

    if missing_packages:
        print_warning(
            f"Install required packages: pip install {' '.join(missing_packages)}"
        )

    # Test Figma API connectivity
    if "requests" not in missing_packages:
        test_code = f"""
import requests
headers = {{"X-Figma-Token": "{figma_pat}"}}
response = requests.get("https://api.figma.com/v1/me", headers=headers)
if response.status_code == 200:
    print(f"Connected to Figma API as: {{response.json().get('email', 'unknown')}}")
    exit(0)
else:
    print(f"Failed to connect to Figma API: {{response.status_code}} {{response.text}}")
    exit(1)
"""
        exit_code, stdout, stderr = run_command(f"python -c '{test_code}'", check=False)

        if exit_code == 0:
            print_success("Successfully connected to Figma API")
            print(f"  {stdout.strip()}")
        else:
            print_error("Failed to connect to Figma API")
            print(f"  {stdout.strip()}")
            print(
                "Check your Figma PAT and make sure it has the necessary permissions."
            )


def check_github_actions():
    """Check GitHub Actions setup."""
    print_header("GitHub Actions")

    # Check for GitHub Actions workflow file
    workflow_dir = ".github/workflows"
    workflow_file = f"{workflow_dir}/orchestra_ci_cd.yml"

    if check_dir_exists(workflow_dir):
        print_success(f"GitHub Actions workflow directory found at {workflow_dir}")
    else:
        print_warning(f"GitHub Actions workflow directory not found at {workflow_dir}")
        print("Run mkdir -p .github/workflows to create it.")
        return

    if check_file_exists(workflow_file):
        print_success(f"GitHub Actions workflow file found at {workflow_file}")
    else:
        print_warning(f"GitHub Actions workflow file not found at {workflow_file}")
        print("This file will be created by the unified_setup.sh script.")

    # Check secrets script
    secrets_script = "scripts/setup_github_org_secrets.sh"
    if check_file_exists(secrets_script):
        print_success(f"GitHub secrets setup script found at {secrets_script}")
    else:
        print_warning(f"GitHub secrets setup script not found at {secrets_script}")


def check_phidata_dependencies():
    """Check for Phidata/Agno dependencies and related libraries."""
    print_header("Phidata/Agno Integration Check")

    # Check core imports
    core_imports = {
        "phi": "Core Phidata package",
        "agno": "Alternative name for Phidata in some contexts",
        "phi.agent": "Agent class for creating AI agents",
        "phi.model.openai": "OpenAI model integration",
        "phi.model.anthropic": "Anthropic model integration",
        "phi.playground": "Phidata UI dashboard",
        "phi.tools": "Phidata tools package",
    }

    missing_core = []
    for module, description in core_imports.items():
        try:
            __import__(module)
            print_success(f"{module}: {description}")
        except ImportError as e:
            print_warning(f"{module}: Not found - {description}")
            missing_core.append(module)

    # Check database dependencies
    db_imports = {
        "psycopg": "PostgreSQL adapter",
        "sqlalchemy": "SQL toolkit and ORM",
        "pgvector": "PostgreSQL vector extension",
    }

    missing_db = []
    for module, description in db_imports.items():
        try:
            __import__(module)
            print_success(f"{module}: {description}")
        except ImportError as e:
            print_warning(f"{module}: Not found - {description}")
            missing_db.append(module)

    # Check tool dependencies
    tool_imports = {
        "duckduckgo_search": "DuckDuckGo search tool",
        "newspaper": "News article extraction tool",
        "wikipedia": "Wikipedia search and retrieval",
        "slack_sdk": "Slack integration",
    }

    missing_tools = []
    for module, description in tool_imports.items():
        try:
            __import__(module)
            print_success(f"{module}: {description}")
        except ImportError as e:
            print_warning(f"{module}: Not found - {description}")
            missing_tools.append(module)

    # Provide guidance based on missing dependencies
    if missing_core or missing_db or missing_tools:
        print_warning("Some Phidata/Agno dependencies are missing.")
        print("\nTo install all required dependencies, run:")
        print("  source ./unified_setup.sh && install_dependencies")

        if missing_core:
            print("\nTo install core Phidata dependencies only:")
            print("  source ./unified_setup.sh && install_dependencies phidata")
    else:
        print_success("All Phidata/Agno dependencies are properly installed.")


def check_memory_manager():
    """Check Memory Manager implementation."""
    print_header("Memory Manager")

    # Check for test file
    memory_test = "test_memory_inmemory.py"
    if check_file_exists(memory_test):
        print_success(f"Memory test script found at {memory_test}")

        # Try running the memory test
        print("Running memory test...")
        exit_code, stdout, stderr = run_command(f"python {memory_test}", check=False)

        if exit_code == 0:
            print_success("Memory test completed successfully")
            # Check for success message in output
            if "Memory system validation PASSED" in stdout:
                print_success("Memory system validation PASSED")
            else:
                print_warning("Memory test completed but validation result unclear")
        else:
            print_error("Memory test failed")
            print(f"  Error: {stderr.strip()}")
    else:
        print_warning(f"Memory test script not found at {memory_test}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}Orchestra Unified Diagnostics{Colors.END}")
    print("=" * 80 + "\n")

    print("Running diagnostics to verify Orchestra setup and configuration...")
    print("This will check all components of the Orchestra system.")

    check_environment()
    check_gcp_auth()
    check_terraform()
    check_figma()
    check_github_actions()
    check_phidata_dependencies()
    check_memory_manager()

    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}Diagnostics Complete{Colors.END}")
    print("=" * 80 + "\n")

    print("Next steps:")
    print("  1. Fix any issues highlighted in red")
    print("  2. Run ./unified_setup.sh to set up missing components")
    print(
        "  3. Install Phidata dependencies: source ./unified_setup.sh && install_dependencies"
    )
    print("  4. Run ./test_memory_inmemory.py to verify memory management")
    print("  5. Run the memory validation script with GCP authentication")
    print("\n")


if __name__ == "__main__":
    main()
