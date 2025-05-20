#!/usr/bin/env python3
"""
Mode System Initializer for AI Orchestra Project

This script initializes the enhanced mode system by setting up the necessary directories
and configuration files. It also provides utilities for migrating from the previous
mode system and setting up the recommended model assignments:

- Gemini 2.5 Pro: architect, review, and orchestrator modes
- GPT-4.1: code and debug modes
- Claude 3.7: strategy, ask, and creative modes

This ensures optimal performance and capabilities for each mode.
"""

import os
import sys
import argparse
import shutil
import logging
import yaml
import colorama
from colorama import Fore, Style
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize colorama
colorama.init()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CORE_DIR = PROJECT_ROOT / "core"
TOOLS_DIR = PROJECT_ROOT / "tools"
DOCS_DIR = PROJECT_ROOT / "docs"

MODE_DEFINITIONS_PATH = CONFIG_DIR / "mode_definitions.yaml"
MODE_MANAGER_PATH = CORE_DIR / "mode_manager.py"
MODE_SWITCHER_PATH = TOOLS_DIR / "mode_switcher.py"
DOCS_PATH = DOCS_DIR / "ENHANCED_MODE_SYSTEM.md"


def print_header():
    """Print the tool header."""
    print(
        f"\n{Fore.CYAN}============================================={Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}{Style.BRIGHT}  AI Orchestra Mode System Initializer{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}============================================={Style.RESET_ALL}\n"
    )


def check_file_exists(path: Path) -> bool:
    """Check if a file exists and print its status."""
    exists = path.exists()
    status = f"{Fore.GREEN}✓ Found" if exists else f"{Fore.RED}✗ Missing"
    print(f"{status}{Style.RESET_ALL} {path.relative_to(PROJECT_ROOT)}")
    return exists


def create_directory(path: Path) -> bool:
    """Create a directory if it doesn't exist."""
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(
                f"{Fore.GREEN}✓ Created directory{Style.RESET_ALL} {path.relative_to(PROJECT_ROOT)}"
            )
            return True
        except Exception as e:
            print(
                f"{Fore.RED}✗ Failed to create directory{Style.RESET_ALL} {path.relative_to(PROJECT_ROOT)}: {str(e)}"
            )
            return False
    else:
        print(
            f"{Fore.GREEN}✓ Directory exists{Style.RESET_ALL} {path.relative_to(PROJECT_ROOT)}"
        )
        return True


def validate_project_structure() -> bool:
    """Validate and set up the project directory structure."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Validating project structure:{Style.RESET_ALL}")

    # Create necessary directories
    directories = [CONFIG_DIR, CORE_DIR, TOOLS_DIR, DOCS_DIR]
    all_created = all(create_directory(directory) for directory in directories)

    if not all_created:
        print(f"\n{Fore.RED}Failed to create required directories{Style.RESET_ALL}")
        return False

    return True


def check_required_files() -> bool:
    """Check if all required files exist."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Checking required files:{Style.RESET_ALL}")

    required_files = [
        MODE_DEFINITIONS_PATH,
        MODE_MANAGER_PATH,
        MODE_SWITCHER_PATH,
        DOCS_PATH,
    ]

    all_exist = all(check_file_exists(file) for file in required_files)

    return all_exist


def initialize_mode_system() -> bool:
    """Initialize the enhanced mode system."""
    print(
        f"\n{Fore.GREEN}{Style.BRIGHT}Initializing enhanced mode system:{Style.RESET_ALL}"
    )

    try:
        # Make sure the project structure is valid
        if not validate_project_structure():
            print(
                f"{Fore.RED}Aborting initialization due to invalid project structure{Style.RESET_ALL}"
            )
            return False

        # Check if all required files exist
        all_files_exist = check_required_files()

        if all_files_exist:
            print(
                f"\n{Fore.GREEN}All required files already exist. Enhanced mode system is ready.{Style.RESET_ALL}"
            )
            return True

        # If files are missing, we need to copy them from templates
        print(
            f"\n{Fore.YELLOW}Some required files are missing. Creating from templates...{Style.RESET_ALL}"
        )

        # Since this script is not supposed to recreate the files (as we've created them separately),
        # we would simply notify the user about what's missing
        print(
            f"\n{Fore.YELLOW}Please run the following commands to create missing files:{Style.RESET_ALL}"
        )

        if not MODE_DEFINITIONS_PATH.exists():
            print(
                f"- Create {MODE_DEFINITIONS_PATH.relative_to(PROJECT_ROOT)} with mode definitions"
            )

        if not MODE_MANAGER_PATH.exists():
            print(
                f"- Create {MODE_MANAGER_PATH.relative_to(PROJECT_ROOT)} to implement mode management logic"
            )

        if not MODE_SWITCHER_PATH.exists():
            print(
                f"- Create {MODE_SWITCHER_PATH.relative_to(PROJECT_ROOT)} for the CLI interface"
            )

        if not DOCS_PATH.exists():
            print(f"- Create {DOCS_PATH.relative_to(PROJECT_ROOT)} for documentation")

        return False

    except Exception as e:
        print(f"{Fore.RED}Error initializing mode system: {str(e)}{Style.RESET_ALL}")
        return False


def verify_model_assignments():
    """Verify the AI model assignments for each mode."""
    print(
        f"\n{Fore.GREEN}{Style.BRIGHT}Verifying AI model assignments:{Style.RESET_ALL}"
    )

    if not MODE_DEFINITIONS_PATH.exists():
        print(
            f"{Fore.RED}Mode definitions file not found. Cannot verify model assignments.{Style.RESET_ALL}"
        )
        return

    try:
        with open(MODE_DEFINITIONS_PATH, "r") as file:
            config = yaml.safe_load(file)

        # Expected model assignments
        expected_assignments = {
            "architect": "gemini-2.5-pro",
            "orchestrator": "gemini-2.5-pro",
            "reviewer": "gemini-2.5-pro",
            "code": "gpt-4.1",
            "debug": "gpt-4.1",
            "strategy": "claude-3.7",
            "ask": "claude-3.7",
            "creative": "claude-3.7",
        }

        # Verify each mode's model assignment
        modes = config.get("modes", {})
        all_correct = True

        for slug, expected_model in expected_assignments.items():
            if slug in modes:
                actual_model = modes[slug].get("model", "").lower()

                if expected_model.lower() in actual_model:
                    print(f"{Fore.GREEN}✓ {slug}: {actual_model}{Style.RESET_ALL}")
                else:
                    print(
                        f"{Fore.RED}✗ {slug}: Expected {expected_model}, got {actual_model}{Style.RESET_ALL}"
                    )
                    all_correct = False
            else:
                print(
                    f"{Fore.YELLOW}! {slug}: Mode not found in configuration{Style.RESET_ALL}"
                )
                all_correct = False

        if all_correct:
            print(
                f"\n{Fore.GREEN}All model assignments are correctly configured.{Style.RESET_ALL}"
            )
        else:
            print(
                f"\n{Fore.YELLOW}Some model assignments need to be updated.{Style.RESET_ALL}"
            )
            print(
                f"Please edit {MODE_DEFINITIONS_PATH.relative_to(PROJECT_ROOT)} to correct the assignments."
            )

    except Exception as e:
        print(f"{Fore.RED}Error verifying model assignments: {str(e)}{Style.RESET_ALL}")


def verify_enhanced_access_permissions():
    """Verify the enhanced access permissions for each mode."""
    print(
        f"\n{Fore.GREEN}{Style.BRIGHT}Verifying enhanced access permissions:{Style.RESET_ALL}"
    )

    if not MODE_DEFINITIONS_PATH.exists():
        print(
            f"{Fore.RED}Mode definitions file not found. Cannot verify access permissions.{Style.RESET_ALL}"
        )
        return

    try:
        with open(MODE_DEFINITIONS_PATH, "r") as file:
            config = yaml.safe_load(file)

        # Modes that should have write access
        write_access_modes = [
            "code",
            "debug",
            "architect",
            "orchestrator",
            "reviewer",
            "strategy",
            "creative",
        ]

        # Verify each mode's write access
        modes = config.get("modes", {})

        for slug, mode_data in modes.items():
            has_write_access = mode_data.get("write_access", False)
            should_have_write_access = slug in write_access_modes

            if has_write_access == should_have_write_access:
                status = f"{Fore.GREEN}✓"
            else:
                status = f"{Fore.RED}✗"

            access_str = "Has write access" if has_write_access else "No write access"
            print(f"{status} {slug}: {access_str}{Style.RESET_ALL}")

            # If it has write access, check if it has file patterns
            if has_write_access:
                file_patterns = mode_data.get("file_patterns", [])
                if file_patterns:
                    print(f"  File patterns: {', '.join(file_patterns)}")
                else:
                    print(
                        f"{Fore.YELLOW}  Warning: Has write access but no file patterns defined{Style.RESET_ALL}"
                    )

    except Exception as e:
        print(
            f"{Fore.RED}Error verifying access permissions: {str(e)}{Style.RESET_ALL}"
        )


def print_workflow_summary():
    """Print a summary of the available workflows."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Available workflows:{Style.RESET_ALL}")

    if not MODE_DEFINITIONS_PATH.exists():
        print(
            f"{Fore.RED}Mode definitions file not found. Cannot show workflows.{Style.RESET_ALL}"
        )
        return

    try:
        with open(MODE_DEFINITIONS_PATH, "r") as file:
            config = yaml.safe_load(file)

        workflows = config.get("workflows", {})

        if not workflows:
            print(
                f"{Fore.YELLOW}No workflows defined in configuration.{Style.RESET_ALL}"
            )
            return

        for slug, workflow in workflows.items():
            print(f"\n{Fore.CYAN}{workflow.get('name', slug)}{Style.RESET_ALL}")
            print(f"Description: {workflow.get('description', 'No description')}")

            steps = workflow.get("steps", [])
            print(f"Steps: {len(steps)}")

            for i, step in enumerate(steps):
                print(
                    f"  {i+1}. [{step.get('mode', 'unknown')}] {step.get('task', 'No task')}"
                )

    except Exception as e:
        print(f"{Fore.RED}Error showing workflows: {str(e)}{Style.RESET_ALL}")


def print_usage_instructions():
    """Print instructions for using the enhanced mode system."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Usage Instructions:{Style.RESET_ALL}")
    print(f"\n1. Switch between modes using the mode switcher tool:")
    print(f"   {Fore.CYAN}python tools/mode_switcher.py --switch code{Style.RESET_ALL}")

    print(f"\n2. Start a workflow:")
    print(
        f"   {Fore.CYAN}python tools/mode_switcher.py --workflow feature_development{Style.RESET_ALL}"
    )

    print(f"\n3. Use interactive mode:")
    print(f"   {Fore.CYAN}python tools/mode_switcher.py --interactive{Style.RESET_ALL}")

    print(f"\n4. Get suggested next steps:")
    print(f"   {Fore.CYAN}python tools/mode_switcher.py --suggestions{Style.RESET_ALL}")

    print(f"\n5. See all available modes and workflows:")
    print(f"   {Fore.CYAN}python tools/mode_switcher.py --list{Style.RESET_ALL}")

    print(
        f"\nFor more details, see the documentation at {Fore.CYAN}docs/ENHANCED_MODE_SYSTEM.md{Style.RESET_ALL}"
    )


def main():
    """Main function for the mode system initializer."""
    parser = argparse.ArgumentParser(
        description="AI Orchestra Mode System Initializer - Set up the enhanced mode system"
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify the existing mode system without initializing",
    )

    args = parser.parse_args()

    print_header()

    if args.verify_only:
        check_required_files()
        verify_model_assignments()
        verify_enhanced_access_permissions()
        print_workflow_summary()
    else:
        success = initialize_mode_system()

        if success:
            verify_model_assignments()
            verify_enhanced_access_permissions()
            print_workflow_summary()
            print_usage_instructions()


if __name__ == "__main__":
    main()
