#!/usr/bin/env python3
"""
Initialize AI Memory System with Performance-First Directives

This script sets up the AI memory system with performance-first directives,
ensuring that all AI assistants working on the project prioritize performance,
optimization, and stability over extensive security measures.
"""

import os
import json
import sys
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("ai-memory-init")

# Directory where this script is located (should be .ai-memory/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Performance-first priorities
PRIORITIES = {
    "name": "Performance-First Directives",
    "version": "1.0.0",
    "timestamp": datetime.now().isoformat(),
    "priorities": {
        "primary": ["performance", "optimization", "stability"],
        "secondary": ["basic_security", "developer_experience"],
    },
    "tokens": {
        "github": ["GH_CLASSIC_PAT_TOKEN", "GH_FINE_GRAINED_TOKEN"],
        "gcp": [
            "GCP_MASTER_SERVICE_JSON",
            "GCP_PROJECT_AUTHENTICATION_EMAIL",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_SECRET_MANAGEMENT_KEY",
            "GCP_WORKLOAD_IDENTITY_PROVIDER",
            "VERTEX_AGENT_KEY",
        ],
    },
    "philosophy": "Single-developer project prioritizing performance over complex security measures",
    "reference_files": ["PROJECT_PRIORITIES.md", "PERFORMANCE_FIRST_README.md"],
    "directives": [
        "Focus on performance and optimization over extensive security",
        "Implement only basic security measures that don't impact performance",
        "Use GitHub and GCP tokens for real-world implementations",
        "Prioritize deployment stability and reliability",
        "Optimize for resource efficiency and scaling",
    ],
    "memory_metadata": {
        "system_wide": True,
        "persistence": "permanent",
        "priority_level": "high",
        "access_control": "all_assistants",
    },
}


def initialize_memory_system():
    """Initialize the AI memory system with performance-first directives."""
    try:
        # Create necessary directories
        os.makedirs(SCRIPT_DIR, exist_ok=True)

        # Special symbolic link to PROJECT_PRIORITIES.md for easier AI access
        priorities_md_path = os.path.join(PROJECT_ROOT, "PROJECT_PRIORITIES.md")
        symlink_path = os.path.join(SCRIPT_DIR, "PROJECT_PRIORITIES.md")

        # Create symbolic link if the file exists
        if os.path.exists(priorities_md_path) and not os.path.exists(symlink_path):
            try:
                os.symlink(priorities_md_path, symlink_path)
                logger.info(f"Created symbolic link to PROJECT_PRIORITIES.md")
            except OSError:
                logger.warning(f"Could not create symbolic link - copying file instead")
                # On systems where symlinks aren't supported (like Windows without admin),
                # copy the file instead
                import shutil

                shutil.copy2(priorities_md_path, symlink_path)

        # Create core memory files

        # 1. Main priorities file
        with open(os.path.join(SCRIPT_DIR, "performance_priorities.json"), "w") as f:
            json.dump(PRIORITIES, f, indent=2)
            logger.info("Created performance_priorities.json in memory system")

        # 2. Index file for quick reference
        with open(os.path.join(SCRIPT_DIR, "memory_index.json"), "w") as f:
            memory_index = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "memory_files": [
                    {
                        "file": "performance_priorities.json",
                        "type": "project_priority",
                        "access": "all_assistants",
                    },
                    {
                        "file": "PROJECT_PRIORITIES.md",
                        "type": "reference",
                        "access": "all_assistants",
                    },
                ],
                "system_directive": "Prioritize performance and optimization over extensive security measures",
            }
            json.dump(memory_index, f, indent=2)
            logger.info("Created memory_index.json in memory system")

        # 3. README for human developers
        with open(os.path.join(SCRIPT_DIR, "README.md"), "w") as f:
            f.write(
                """# AI Memory System

This directory contains memory files used by AI assistants working on this project.

## Purpose

These files establish the project's performance-first philosophy in the AI memory system,
ensuring all AI tools prioritize performance, optimization, and stability over extensive
security measures.

## Important Files

- `performance_priorities.json`: Core priorities configuration
- `memory_index.json`: Index of memory files for AI assistants
- Symbolic links to relevant documentation

## Maintenance

This directory is maintained by:
- `update_ai_memory_priorities.py` script
- The `apply_performance_priorities.sh` script with the --update-all flag

Do not modify these files directly unless you specifically want to change the 
project priorities.
"""
            )
            logger.info("Created README.md in memory system")

        logger.info("Successfully initialized AI memory system with performance-first directives")
        return True

    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        return False


if __name__ == "__main__":
    success = initialize_memory_system()
    sys.exit(0 if success else 1)
