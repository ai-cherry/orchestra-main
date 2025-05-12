"""
Main entry point for the GCP migration toolkit.

This module serves as the entry point for command-line execution
of the migration toolkit.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow module imports
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.append(str(parent_dir))

from gcp_migration.application.cli import cli

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set more specific log levels for noisy libraries
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('google.auth.transport').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


def main():
    """Execute the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()