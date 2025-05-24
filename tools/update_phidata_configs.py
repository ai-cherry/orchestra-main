#!/usr/bin/env python
"""
Helper script to update existing Phidata agent configurations with UI optimization settings.

This script:
1. Scans a directory for YAML files containing Phidata agent configurations
2. Updates them to include settings for optimal UI display (markdown, show_tool_calls)
3. Adds storage and memory configurations if missing

Usage:
  python tools/update_phidata_configs.py --config-dir /path/to/configs [--dry-run]
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, Tuple

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def is_phidata_agent_config(config: Dict[str, Any]) -> bool:
    """
    Check if a dictionary is a Phidata agent configuration.

    Args:
        config: Dictionary to check

    Returns:
        True if it's a Phidata agent config, False otherwise
    """
    # Check for wrapper_type = phidata or phidata_agent_class
    return isinstance(config, dict) and (config.get("wrapper_type") == "phidata" or "phidata_agent_class" in config)


def update_agent_config(config: Dict[str, Any], agent_key: str) -> Tuple[Dict[str, Any], bool]:
    """
    Update a Phidata agent configuration with optimal UI display settings.

    Args:
        config: Agent configuration dictionary
        agent_key: Key of the agent in the parent dictionary

    Returns:
        Tuple of (updated config, whether changes were made)
    """
    agent_config = config[agent_key]
    changes_made = False

    # Only process Phidata agent configurations
    if not is_phidata_agent_config(agent_config):
        return config, False

    # Add markdown: true if missing
    if "markdown" not in agent_config:
        agent_config["markdown"] = True
        changes_made = True
        logger.info(f"Added markdown: true to {agent_key}")

    # Add show_tool_calls based on environment
    is_prod = "prod" in agent_key.lower()
    if "show_tool_calls" not in agent_config:
        # Hide tool calls in production for cleaner UI, show in dev for debugging
        agent_config["show_tool_calls"] = not is_prod
        changes_made = True
        logger.info(f"Added show_tool_calls: {not is_prod} to {agent_key}")

    # Add storage configuration if missing
    if "storage" not in agent_config:
        agent_config["storage"] = {
            "table_name": f"{agent_key}_storage".lower(),
            "schema_name": "llm",
        }
        changes_made = True
        logger.info(f"Added storage configuration to {agent_key}")

    # Add memory configuration if missing
    if "memory" not in agent_config:
        agent_config["memory"] = {
            "table_name": f"{agent_key}_memory".lower(),
            "schema_name": "llm",
        }
        changes_made = True
        logger.info(f"Added memory configuration to {agent_key}")

    # For team configurations, update team_markdown and member settings
    if "members" in agent_config and isinstance(agent_config["members"], list):
        # Add team_markdown setting
        if "team_markdown" not in agent_config:
            agent_config["team_markdown"] = True
            changes_made = True
            logger.info(f"Added team_markdown: true to {agent_key}")

        # Update each member
        for i, member in enumerate(agent_config["members"]):
            if "markdown" not in member:
                member["markdown"] = True
                changes_made = True
                logger.info(f"Added markdown: true to member {i+1} in {agent_key}")

            # Add show_tool_calls based on environment
            if "show_tool_calls" not in member:
                member["show_tool_calls"] = not is_prod
                changes_made = True
                logger.info(f"Added show_tool_calls: {not is_prod} to member {i+1} in {agent_key}")

    config[agent_key] = agent_config
    return config, changes_made


def process_yaml_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Process a YAML file to update Phidata agent configurations.

    Args:
        file_path: Path to the YAML file
        dry_run: If True, don't actually write changes

    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            logger.warning(f"Skipping {file_path}: Not a valid YAML dictionary")
            return False

        any_changes = False

        # Process each key that might be a Phidata agent configuration
        for key in list(config.keys()):
            if isinstance(config[key], dict):
                config, changes = update_agent_config(config, key)
                any_changes = any_changes or changes

        # Write changes if any were made
        if any_changes and not dry_run:
            with open(file_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Updated {file_path}")
        elif any_changes:
            logger.info(f"Would update {file_path} (dry run)")

        return any_changes

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False


def process_directory(directory: str, dry_run: bool = False) -> Tuple[int, int]:
    """
    Process all YAML files in a directory.

    Args:
        directory: Directory path
        dry_run: If True, don't actually write changes

    Returns:
        Tuple of (files processed, files changed)
    """
    files_processed = 0
    files_changed = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                file_path = os.path.join(root, file)
                files_processed += 1

                if process_yaml_file(file_path, dry_run):
                    files_changed += 1

    return files_processed, files_changed


def main():
    parser = argparse.ArgumentParser(description="Update Phidata agent configs with UI optimization settings")
    parser.add_argument(
        "--config-dir",
        required=True,
        help="Directory containing agent configuration YAML files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write changes, just show what would be changed",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.config_dir):
        logger.error(f"Config directory {args.config_dir} does not exist")
        sys.exit(1)

    logger.info(f"Processing YAML files in {args.config_dir}" + (" (dry run)" if args.dry_run else ""))

    files_processed, files_changed = process_directory(args.config_dir, args.dry_run)

    logger.info(f"Processed {files_processed} YAML files, updated {files_changed} files")

    if files_changed > 0:
        logger.info("Changes made to Phidata agent configurations:")
        logger.info("- Added markdown: true for better UI formatting")
        logger.info("- Added show_tool_calls settings (hidden in prod for cleaner UI)")
        logger.info("- Added storage/memory configurations for session persistence")

        if args.dry_run:
            logger.info("This was a dry run. No files were actually modified.")
            logger.info("Run without --dry-run to apply these changes.")
    else:
        logger.info("No changes needed to Phidata agent configurations.")


if __name__ == "__main__":
    main()
