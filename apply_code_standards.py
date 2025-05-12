#!/usr/bin/env python3
"""
Apply code standards to the codebase.

This script applies the standardized code style and error handling patterns
defined in CODE_STYLE_GUIDE.md across the entire codebase, including:

1. Formatting Python files using Black
2. Sorting imports using isort
3. Running flake8 to identify remaining issues
4. Formatting Terraform files using terraform fmt
5. Validating Terr    parser.add_argument(
        "--no-pre-commit",
        action="store_true",
        help="Skip pre-commit setup"
    )
    parser.add_argument(
        "--no-terraform",
        action="store_true",
        help="Skip Terraform formatting"
    )
    parser.add_argument(
        "--no-terraform-validate",
        action="store_true",
        help="Skip Terraform validation"
    )
    parser.add_argument(
        "--no-tflint",
        action="store_true",
        help="Skip Terraform linting with tflint"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    ) using terraform validate
6. Running tflint for Terraform linting
7. Setting up pre-commit hooks for automated checks

Usage:
    python apply_code_standards.py [directories...]

If no directories are provided, the script will process the entire project.
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import List, Optional, Tuple


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("apply_code_standards")


def run_command(command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
    """
    Run a shell command and return the result.

    Args:
        command: The command to run as a list of strings
        cwd: The directory to run the command in

    Returns:
        A tuple of (success, output)
    """
    logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        success = result.returncode == 0
        output = result.stdout

        if not success:
            logger.warning(f"Command failed: {' '.join(command)}")
            logger.warning(f"Output: {output}")

        return success, output
    except Exception as e:
        logger.error(f"Error running command {' '.join(command)}: {str(e)}")
        return False, str(e)


def is_tool_installed(tool: str) -> bool:
    """
    Check if a command-line tool is installed.

    Args:
        tool: The name of the tool to check

    Returns:
        True if the tool is installed, False otherwise
    """
    success, _ = run_command(["which", tool])
    return success


def apply_black(directories: List[str]) -> bool:
    """
    Apply Black formatting to Python files.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("black"):
        logger.error("Black is not installed. Install it with: pip install black")
        return False

    logger.info("Applying Black formatting...")

    # Use pyproject.toml for configuration
    command = ["black"]
    command.extend(directories)

    success, output = run_command(command)
    if success:
        logger.info("Black formatting applied successfully")
    else:
        logger.error("Black formatting failed")

    return success


def apply_isort(directories: List[str]) -> bool:
    """
    Apply isort to sort imports.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("isort"):
        logger.error("isort is not installed. Install it with: pip install isort")
        return False

    logger.info("Sorting imports with isort...")

    # Use pyproject.toml for configuration
    command = ["isort"]
    command.extend(directories)

    success, output = run_command(command)
    if success:
        logger.info("Imports sorted successfully")
    else:
        logger.error("Import sorting failed")

    return success


def run_flake8(directories: List[str]) -> bool:
    """
    Run flake8 to check for linting issues.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("flake8"):
        logger.error("flake8 is not installed. Install it with: pip install flake8")
        return False

    logger.info("Running flake8 to check for linting issues...")

    # Use .flake8 for configuration
    command = ["flake8"]
    command.extend(directories)

    success, output = run_command(command)
    if success:
        logger.info("No flake8 issues found")
    else:
        logger.warning("flake8 issues found:")
        print(output)

    return success


def format_terraform(directories: List[str]) -> bool:
    """
    Format Terraform files using terraform fmt.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("terraform"):
        logger.error("Terraform is not installed. Install it following the instructions at: "
                     "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli")
        return False

    logger.info("Formatting Terraform files...")

    # Get all .tf files in the specified directories
    tf_files = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".tf"):
                    tf_files.append(os.path.join(root, file))

    if not tf_files:
        logger.info("No Terraform files found in the specified directories")
        return True

    logger.info(f"Found {len(tf_files)} Terraform files to format")

    # Format each file directory
    tf_dirs = set(os.path.dirname(file) for file in tf_files)

    results = []
    for tf_dir in tf_dirs:
        logger.debug(f"Formatting Terraform files in directory: {tf_dir}")
        command = ["terraform", "fmt"]
        success, output = run_command(command, cwd=tf_dir)
        results.append(success)

        if not success:
            logger.warning(f"Terraform formatting failed in directory {tf_dir}")
            logger.warning(f"Output: {output}")
        else:
            logger.debug(f"Terraform formatting succeeded in directory {tf_dir}")

    if all(results):
        logger.info("All Terraform files formatted successfully")
        return True
    else:
        logger.error("Terraform formatting failed in some directories")
        return False


def validate_terraform(directories: List[str]) -> bool:
    """
    Validate Terraform files using terraform validate.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("terraform"):
        logger.error("Terraform is not installed. Install it following the instructions at: "
                     "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli")
        return False

    logger.info("Validating Terraform configurations...")

    # Find all directories containing .tf files
    tf_dirs = set()
    for directory in directories:
        for root, _, files in os.walk(directory):
            if any(file.endswith(".tf") for file in files):
                tf_dirs.add(root)

    if not tf_dirs:
        logger.info("No Terraform configurations found in the specified directories")
        return True

    logger.info(f"Found {len(tf_dirs)} Terraform configuration directories to validate")

    # Validate each directory with terraform configurations
    results = []
    for tf_dir in tf_dirs:
        logger.debug(f"Validating Terraform configuration in directory: {tf_dir}")

        # First run terraform init if .terraform directory doesn't exist
        if not os.path.exists(os.path.join(tf_dir, ".terraform")):
            logger.info(f"Initializing Terraform in {tf_dir}")
            init_command = ["terraform", "init", "-backend=false"]
            init_success, init_output = run_command(init_command, cwd=tf_dir)

            if not init_success:
                logger.warning(f"Terraform initialization failed in {tf_dir}, skipping validation")
                logger.warning(f"Output: {init_output}")
                results.append(False)
                continue

        # Now run terraform validate
        validate_command = ["terraform", "validate"]
        success, output = run_command(validate_command, cwd=tf_dir)
        results.append(success)

        if not success:
            logger.warning(f"Terraform validation failed in directory {tf_dir}")
            logger.warning(f"Output: {output}")
        else:
            logger.debug(f"Terraform validation succeeded in directory {tf_dir}")

    if all(results):
        logger.info("All Terraform configurations validated successfully")
        return True
    else:
        logger.error("Terraform validation failed in some directories")
        return False


def run_tflint(directories: List[str]) -> bool:
    """
    Run tflint to check for Terraform linting issues.

    Args:
        directories: List of directories to process

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("tflint"):
        logger.error("tflint is not installed. Install it following the instructions at: "
                     "https://github.com/terraform-linters/tflint#installation")
        return False

    logger.info("Running tflint to check for Terraform linting issues...")

    # Find all directories containing .tf files
    tf_dirs = set()
    for directory in directories:
        for root, _, files in os.walk(directory):
            if any(file.endswith(".tf") for file in files):
                tf_dirs.add(root)

    if not tf_dirs:
        logger.info("No Terraform configurations found in the specified directories")
        return True

    logger.info(f"Found {len(tf_dirs)} Terraform configuration directories to lint")

    # Lint each directory with terraform configurations
    results = []
    for tf_dir in tf_dirs:
        logger.debug(f"Linting Terraform configuration in directory: {tf_dir}")
        command = ["tflint", "--format=compact"]
        success, output = run_command(command, cwd=tf_dir)
        results.append(success)

        if not success:
            logger.warning(f"tflint found issues in directory {tf_dir}")
            logger.warning(f"Output: {output}")
            print(output)  # Print issues to console
        else:
            logger.debug(f"tflint found no issues in directory {tf_dir}")

    if all(results):
        logger.info("No tflint issues found in Terraform configurations")
        return True
    else:
        logger.warning("tflint found issues in some Terraform configurations")
        return True  # Return True even with issues to not block the process


def setup_pre_commit() -> bool:
    """
    Set up the pre-commit hooks.

    Returns:
        True if successful, False otherwise
    """
    if not is_tool_installed("pre-commit"):
        logger.error("pre-commit is not installed. Install it with: pip install pre-commit")
        return False

    logger.info("Setting up pre-commit hooks...")

    success, output = run_command(["pre-commit", "install"])
    if success:
        logger.info("Pre-commit hooks installed successfully")
    else:
        logger.error("Failed to install pre-commit hooks")

    return success


def main() -> int:
    """
    Main function.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Apply code standards to the codebase")
    parser.add_argument(
        "directories",
        nargs="*",
        help="Directories to process (default: the entire project)"
    )
    parser.add_argument(
        "--no-black",
        action="store_true",
        help="Skip Black formatting"
    )
    parser.add_argument(
        "--no-isort",
        action="store_true",
        help="Skip isort formatting"
    )
    parser.add_argument(
        "--no-flake8",
        action="store_true",
        help="Skip flake8 linting"
    )
    parser.add_argument(
        "--no-pre-commit",
        action="store_true",
        help="Skip pre-commit setup"
    )
    parser.add_argument(
        "--no-terraform",
        action="store_true",
        help="Skip Terraform formatting"
    )
    parser.add_argument(
        "--no-terraform-validate",
        action="store_true",
        help="Skip Terraform validation"
    )
    parser.add_argument(
        "--no-tflint",
        action="store_true",
        help="Skip tflint linting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Use default directories if none provided
    directories = args.directories or [
        "ai-orchestra",
        "gcp_migration",
        "mcp_server",
        "services",
        "wif_implementation",
        "utils",
        "examples",
    ]

    # Filter out non-existent directories
    directories = [d for d in directories if os.path.exists(d)]

    if not directories:
        logger.error("No valid directories to process")
        return 1

    logger.info(f"Processing directories: {', '.join(directories)}")

    # Apply standards
    results = []

    if not args.no_black:
        results.append(apply_black(directories))

    if not args.no_isort:
        results.append(apply_isort(directories))

    if not args.no_flake8:
        results.append(run_flake8(directories))

    if not args.no_terraform:
        results.append(format_terraform(directories))

    if not args.no_terraform_validate:
        results.append(validate_terraform(directories))

    if not args.no_tflint:
        results.append(run_tflint(directories))

    if not args.no_pre_commit:
        results.append(setup_pre_commit())

    # Check if any operation failed
    if all(results):
        logger.info("All code standards applied successfully!")
        return 0
    else:
        logger.warning("Some operations failed. Check the log for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
