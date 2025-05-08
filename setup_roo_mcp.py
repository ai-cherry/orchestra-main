#!/usr/bin/env python3
"""
Setup script for Roo-MCP integration.

This script sets up the necessary environment for the Roo-MCP integration,
including installing dependencies, configuring paths, and verifying the setup.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("roo-mcp-setup")


def check_python_version() -> bool:
    """
    Check if the Python version is compatible.
    
    Returns:
        bool: True if the Python version is compatible, False otherwise.
    """
    required_version = (3, 11)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        logger.info(f"Python version {'.'.join(map(str, current_version))} is compatible.")
        return True
    else:
        logger.error(
            f"Python version {'.'.join(map(str, current_version))} is not compatible. "
            f"Required version: {'.'.join(map(str, required_version))} or higher."
        )
        return False


def install_dependencies(use_poetry: bool = True) -> bool:
    """
    Install the required dependencies.
    
    Args:
        use_poetry: Whether to use Poetry for dependency management.
        
    Returns:
        bool: True if dependencies were installed successfully, False otherwise.
    """
    try:
        if use_poetry:
            logger.info("Installing dependencies using Poetry...")
            
            # Check if Poetry is installed
            try:
                subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("Poetry not found. Installing Poetry...")
                subprocess.run(
                    ["curl", "-sSL", "https://install.python-poetry.org", "|", "python3", "-"],
                    shell=True,
                    check=True
                )
            
            # Install dependencies
            subprocess.run(["poetry", "install"], check=True)
            logger.info("Dependencies installed successfully using Poetry.")
        else:
            logger.info("Installing dependencies using pip...")
            
            # Create requirements.txt if it doesn't exist
            if not os.path.exists("requirements.txt"):
                with open("requirements.txt", "w") as f:
                    f.write("pydantic>=2.0.0\n")
                    f.write("fastapi>=0.100.0\n")
                    f.write("uvicorn>=0.22.0\n")
                    f.write("aiohttp>=3.8.4\n")
                    f.write("python-dotenv>=1.0.0\n")
            
            # Install dependencies
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            logger.info("Dependencies installed successfully using pip.")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def setup_environment() -> bool:
    """
    Set up the environment for the Roo-MCP integration.
    
    Returns:
        bool: True if the environment was set up successfully, False otherwise.
    """
    try:
        # Add the current directory to PYTHONPATH
        project_root = os.path.abspath(os.path.dirname(__file__))
        
        # Create .env file if it doesn't exist
        env_path = os.path.join(project_root, ".env")
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write(f"PYTHONPATH={project_root}\n")
                f.write("MCP_SERVER_HOST=localhost\n")
                f.write("MCP_SERVER_PORT=8000\n")
        
        # Export PYTHONPATH
        os.environ["PYTHONPATH"] = project_root
        
        logger.info(f"Environment set up successfully. Project root: {project_root}")
        return True
    except Exception as e:
        logger.error(f"Failed to set up environment: {e}")
        return False


def verify_setup() -> bool:
    """
    Verify that the setup is correct.
    
    Returns:
        bool: True if the setup is correct, False otherwise.
    """
    try:
        # Try importing key modules
        import_checks = [
            "import pydantic",
            "from mcp_server.roo import modes, transitions, memory_hooks, rules",
            "from mcp_server.roo.adapters import gemini_adapter"
        ]
        
        for check in import_checks:
            try:
                exec(check)
                logger.info(f"Import check passed: {check}")
            except ImportError as e:
                logger.error(f"Import check failed: {check} - {e}")
                return False
        
        logger.info("All import checks passed. Setup verified successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to verify setup: {e}")
        return False


def main() -> int:
    """
    Main function.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(description="Setup script for Roo-MCP integration.")
    parser.add_argument("--no-poetry", action="store_true", help="Use pip instead of Poetry for dependency management.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Roo-MCP integration setup...")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies(not args.no_poetry):
        return 1
    
    # Set up environment
    if not setup_environment():
        return 1
    
    # Verify setup
    if not verify_setup():
        return 1
    
    logger.info("Roo-MCP integration setup completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())