"""
Gemini Configuration Service for GCP Migration.

This module provides specialized functionality for setting up and managing
Gemini Code Assist configuration for GCP Workstations.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gcp_migration.domain.exceptions import ConfigurationError
from gcp_migration.domain.interfaces_ext import IGeminiConfigService
from gcp_migration.infrastructure.extended_gcp_service import ExtendedGCPService

# Configure logging
logger = logging.getLogger(__name__)


class GeminiConfigService(IGeminiConfigService):
    """
    Service for setting up and managing Gemini Code Assist configuration.
    Implements the IGeminiConfigService interface.
    """

    def __init__(self, gcp_service: Optional[ExtendedGCPService] = None):
        """
        Initialize the Gemini Config service.

        Args:
            gcp_service: Optional ExtendedGCPService instance (will create one if None)
        """
        self.gcp_service = gcp_service or ExtendedGCPService()

        # Paths for Gemini configurations
        self._home_dir = Path.home()
        self._config_dir = self._home_dir / ".config" / "Google" / "CloudCodeAI"
        self._config_file = self._config_dir / "gemini-code-assist.yaml"

        # VS Code extension paths
        self._vscode_ext_dir = self._home_dir / ".vscode" / "extensions"
        self._extension_id = "Google.cloud-code"

        # Memory system paths
        self._memory_dir = self._home_dir / ".ai-memory"
        self._memory_index_file = self._memory_dir / "memory_index.json"

    def setup_gemini_config(self, config_path: Optional[str] = None) -> str:
        """
        Set up Gemini Code Assist configuration for use in GCP Workstations.

        This method creates or updates the Gemini Code Assist configuration file,
        which is required for the VS Code extension to communicate with the Gemini API.
        It will create any necessary directories and substitute project-specific
        variables in the configuration.

        Args:
            config_path: Optional custom path to write the configuration file.
                         If not provided, defaults to ~/.config/Google/CloudCodeAI/gemini-code-assist.yaml

        Returns:
            Path to the generated configuration file as a string

        Raises:
            ConfigurationError: If configuration setup fails for any reason,
                                including file access errors or missing templates

        Example:
            ```python
            gemini_service = GeminiConfigService()
            config_path = gemini_service.setup_gemini_config()
            print(f"Gemini configured at: {config_path}")
            ```
        """
        try:
            # Use provided path or default
            if config_path:
                config_file = Path(config_path)
                config_dir = config_file.parent
            else:
                config_dir = self._config_dir
                config_file = self._config_file

            # Create config directory if it doesn't exist
            config_dir.mkdir(parents=True, exist_ok=True)

            # Get template configuration
            template_path = (
                Path(__file__).parent.parent
                / "docker"
                / "workstation-image"
                / "gemini-code-assist.yaml"
            )

            if not template_path.exists():
                # If template doesn't exist, create a minimal default configuration
                logger.warning(
                    f"Template not found at {template_path}, creating default configuration"
                )
                config_content = self._create_default_config()
            else:
                # Read template configuration
                with open(template_path, "r") as f:
                    config_content = f.read()

            # Replace variables
            project_id = self.gcp_service.project_id or "unknown-project"
            config_content = config_content.replace("${GCP_PROJECT_ID}", project_id)

            # Write to target path
            with open(config_file, "w") as f:
                f.write(config_content)

            logger.info(f"Set up Gemini Code Assist configuration at {config_file}")
            return str(config_file)
        except Exception as e:
            error_msg = f"Failed to setup Gemini config: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def setup_mcp_memory(self, memory_path: Optional[str] = None) -> str:
        """
        Set up MCP memory system for AI assistants.

        Args:
            memory_path: Path for MCP memory (optional)

        Returns:
            Path to the MCP memory directory

        Raises:
            ConfigurationError: If setup fails
        """
        try:
            # Use provided path or default
            if memory_path:
                memory_dir = Path(memory_path)
            else:
                memory_dir = self._memory_dir

            # Create memory directory if it doesn't exist
            memory_dir.mkdir(parents=True, exist_ok=True)

            # Create memory index
            memory_index = {
                "version": "1.0",
                "environment": "gcp-workstation",
                "memory_format": "vector",
                "memory_location": "firestore",
                "project_id": self.gcp_service.project_id,
                "storage_options": {
                    "persistent": True,
                    "encrypted": True,
                    "geo_redundant": True,
                },
                "assistants": [
                    {
                        "name": "gemini",
                        "type": "code-assist",
                        "provider": "google",
                        "enabled": True,
                        "model": "gemini-1.5-pro",
                    },
                    {
                        "name": "roo",
                        "type": "chat",
                        "provider": "anthropic",
                        "enabled": True,
                        "model": "claude-3-sonnet",
                    },
                    {
                        "name": "cline",
                        "type": "chat",
                        "provider": "anthropic",
                        "enabled": True,
                        "model": "claude-3-opus",
                    },
                ],
            }

            # Write memory index
            with open(memory_dir / "memory_index.json", "w") as f:
                json.dump(memory_index, f, indent=2)

            logger.info(f"Set up MCP memory system at {memory_dir}")
            return str(memory_dir)
        except IOError as io_error:
            error_msg = f"I/O error during MCP memory setup: {str(io_error)}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(message=error_msg, cause=io_error)
        except PermissionError as perm_error:
            error_msg = f"Permission denied when creating MCP memory directory: {str(perm_error)}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(message=error_msg, cause=perm_error)
        except Exception as e:
            error_msg = f"Failed to setup MCP memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(message=error_msg, cause=e)

    def verify_installation(self) -> Dict[str, bool]:
        """
        Verify that Gemini Code Assist is installed and configured.

        Returns:
            Dictionary with verification results

        Raises:
            ConfigurationError: If verification fails
        """
        try:
            # Check configuration files
            config_exists = self._config_file.exists()

            # Check VS Code extension
            extension_installed = self._check_extension_installed()

            # Check memory system
            memory_exists = (
                self._memory_dir.exists() and self._memory_index_file.exists()
            )

            # Check Vertex AI API
            vertex_api_enabled = False
            apis = self.gcp_service.check_gcp_apis_enabled()
            if "aiplatform.googleapis.com" in apis:
                vertex_api_enabled = apis["aiplatform.googleapis.com"]

            # Return results
            return {
                "config_exists": config_exists,
                "extension_installed": extension_installed,
                "memory_exists": memory_exists,
                "vertex_api_enabled": vertex_api_enabled,
            }
        except Exception as e:
            error_msg = f"Failed to verify Gemini installation: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def install_vscode_extension(self) -> bool:
        """
        Install VS Code extension for Gemini Code Assist.

        Returns:
            True if installation was successful

        Raises:
            ConfigurationError: If installation fails
        """
        try:
            # Check if already installed
            if self._check_extension_installed():
                logger.info("Gemini Code Assist extension already installed")
                return True

            # Install extension using VS Code CLI
            logger.info("Installing Gemini Code Assist extension")
            result = subprocess.run(
                ["code", "--install-extension", "Google.cloud-code", "--force"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = f"Failed to install extension: {result.stderr}"
                logger.error(error_msg)
                raise ConfigurationError(message=error_msg)

            logger.info("Successfully installed Gemini Code Assist extension")
            return True
        except Exception as e:
            error_msg = f"Failed to install VS Code extension: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def backup_existing_config(self) -> Optional[str]:
        """
        Backup existing Gemini configuration files.

        Returns:
            Path to backup directory, or None if no backup was needed

        Raises:
            ConfigurationError: If backup fails
        """
        try:
            # Check if config exists
            if not self._config_file.exists():
                return None

            # Create backup directory
            backup_dir = self._config_dir / "backup"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped backup filename
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = backup_dir / f"gemini-code-assist.{timestamp}.yaml"

            # Copy config to backup
            shutil.copy2(self._config_file, backup_file)

            logger.info(f"Backed up configuration to {backup_file}")
            return str(backup_file)
        except Exception as e:
            error_msg = f"Failed to backup Gemini configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def _check_extension_installed(self) -> bool:
        """
        Check if VS Code extension is installed.

        Returns:
            True if extension is installed
        """
        # First check through VS Code CLI if available
        try:
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True,
                check=True,
            )

            if self._extension_id in result.stdout:
                return True
        except:
            # Fallback to checking extension directory
            if self._vscode_ext_dir.exists():
                for ext_dir in self._vscode_ext_dir.glob("Google.cloud-code*"):
                    if ext_dir.is_dir():
                        return True

        return False

    def _create_default_config(self) -> str:
        """
        Create a default Gemini Code Assist configuration.

        Returns:
            Default configuration content
        """
        config = f"""# Default Gemini Code Assist configuration
project_id: {self.gcp_service.project_id or "unknown-project"}
region: us-central1
enable_code_generation: true
enable_code_completion: true
enable_code_chat: true
enable_code_actions: true
verbosity: info

models:
  - name: gemini-1.5-pro
    type: code
    default: true

settings:
  max_tokens: 8192
  temperature: 0.2
  top_p: 0.95
  top_k: 40
"""
        return config
