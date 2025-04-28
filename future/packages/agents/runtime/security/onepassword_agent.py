"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This legacy file has been replaced by a newer implementation with improved architecture 
and error handling. Please consult the project documentation for the recommended 
replacement module.

Example migration:
from onepassword_agent import * # Old
# Change to:
# Import the appropriate replacement module
"""

"""
1Password Agent for Orchestra.

This module implements an agent that interacts with 1Password for secure credential management.
It provides methods for retrieving, managing, and securing API keys and other credentials
required by various agents and services within the Orchestra system.
"""

import logging
import json
import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Union
import asyncio

from orchestrator.agents.agent_base import Agent

logger = logging.getLogger(__name__)


class OnePasswordAgent(Agent):
    """
    Agent that securely interacts with 1Password to manage credentials.

    This agent provides a secure interface for other agents and services to access
    credentials stored in 1Password, handling authentication, retrieval, and temporary
    access to secrets without exposing them unnecessarily.
    """

    def __init__(
        self,
        agent_id: str = "onepassword-agent",
        name: str = "1Password Agent",
        description: str = "Manages secure access to credentials via 1Password",
        op_path: Optional[str] = None,
        service_account_token: Optional[str] = None,
    ):
        """
        Initialize the 1Password Agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of agent's purpose
            op_path: Path to the 1Password CLI executable (op)
            service_account_token: Service account token for non-interactive authentication
        """
        super().__init__(agent_id, name, description)
        self.op_path = op_path or self._find_op_executable()
        self.service_account_token = service_account_token
        self.authenticated = False
        self.session_token = None
        self.default_vault = "Orchestra"

    async def initialize(self) -> None:
        """Initialize the agent and authenticate with 1Password."""
        await super().initialize()

        if not self.op_path:
            logger.error("1Password CLI not found. Cannot initialize OnePasswordAgent.")
            return

        try:
            # Attempt to authenticate using the service account token
            if self.service_account_token:
                await self._authenticate_with_service_account()
            else:
                logger.warning(
                    "No service account token provided. Manual authentication will be required."
                )

            logger.info("1Password Agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize 1Password Agent: {str(e)}")

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """
        Process a credential access request.

        Args:
            input_text: The request text
            context: Additional context information

        Returns:
            Response message (never includes actual credentials)
        """
        context = context or {}

        # Extract request details
        request_type = context.get("request_type", "unknown")

        if not self.authenticated:
            return "Authentication required before accessing 1Password credentials."

        if request_type == "credential_exists":
            item_name = context.get("item_name", "")
            vault = context.get("vault", self.default_vault)
            exists = await self.check_credential_exists(item_name, vault)
            return f"Credential '{item_name}' {'exists' if exists else 'does not exist'} in vault '{vault}'."

        elif request_type == "list_available_credentials":
            vault = context.get("vault", self.default_vault)
            category = context.get("category", None)
            credentials = await self.list_available_credentials(vault, category)

            if not credentials:
                return f"No credentials found in vault '{vault}'" + (
                    f" with category '{category}'" if category else ""
                )

            return (
                f"Available credentials in vault '{vault}'"
                + (f" with category '{category}'" if category else "")
                + f": {len(credentials)}"
            )

        elif request_type == "inject_credentials":
            # This won't return actual credentials but confirms they were injected
            target = context.get("target", "")
            item_names = context.get("item_names", [])

            if not item_names:
                return "No credential names provided for injection."

            if not target:
                return "No target provided for credential injection."

            # Just return confirmation that the credentials would be injected
            return f"Credentials would be securely injected into {target}."

        else:
            return "Unknown credential request type. Please specify a valid request_type in the context."

    async def _authenticate_with_service_account(self) -> bool:
        """
        Authenticate with 1Password using a service account token.

        Returns:
            True if authentication succeeded, False otherwise
        """
        if not self.service_account_token:
            logger.error("No service account token provided")
            return False

        try:
            # Use a tempfile to store the token to avoid it appearing in process args
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as token_file:
                token_file.write(self.service_account_token)
                token_file_path = token_file.name

            # Execute authentication command
            proc = await asyncio.create_subprocess_exec(
                self.op_path,
                "signin",
                "--raw",
                "--account",
                "orchestraai.1password.com",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Read token and pass to stdin
            with open(token_file_path, "r") as f:
                token = f.read()

            stdout, stderr = await proc.communicate(input=token.encode())
            os.unlink(token_file_path)  # Securely delete the token file

            if proc.returncode != 0:
                logger.error(f"1Password authentication failed: {stderr.decode()}")
                return False

            # Store session token securely
            self.session_token = stdout.decode().strip()
            self.authenticated = True
            logger.info("Successfully authenticated with 1Password")
            return True

        except Exception as e:
            logger.error(f"Error during 1Password authentication: {str(e)}")
            return False

    async def get_credential(
        self, item_name: str, field: str = None, vault: str = None
    ) -> Optional[str]:
        """
        Get a credential from 1Password.

        Args:
            item_name: The name of the item in 1Password
            field: The specific field to get (default: password)
            vault: The vault to use (default: self.default_vault)

        Returns:
            The credential value, or None if it could not be retrieved
        """
        if not self.authenticated:
            logger.error("Not authenticated with 1Password")
            return None

        vault = vault or self.default_vault
        field_arg = ["--fields", field] if field else []

        try:
            # Build the command to get the item
            cmd = [
                self.op_path,
                "item",
                "get",
                item_name,
                "--vault",
                vault,
                "--format",
                "json",
            ]
            cmd.extend(field_arg)

            # Set up environment with session token
            env = os.environ.copy()
            env["OP_SESSION_TOKEN"] = self.session_token

            # Execute the command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(
                    f"Failed to get credential '{item_name}': {stderr.decode()}"
                )
                return None

            result = json.loads(stdout.decode())

            # Extract the credential based on field
            if field:
                # If specific field was requested, it should be in the output
                return result
            else:
                # Otherwise extract the password
                for section in result.get("fields", []):
                    if section.get("id") == "password":
                        return section.get("value")

                logger.warning(f"No password field found for '{item_name}'")
                return None

        except Exception as e:
            logger.error(f"Error getting credential '{item_name}': {str(e)}")
            return None

    async def check_credential_exists(self, item_name: str, vault: str = None) -> bool:
        """
        Check if a credential exists in 1Password.

        Args:
            item_name: The name of the item to check
            vault: The vault to use (default: self.default_vault)

        Returns:
            True if the credential exists, False otherwise
        """
        if not self.authenticated:
            logger.error("Not authenticated with 1Password")
            return False

        vault = vault or self.default_vault

        try:
            # Build the command to list items
            cmd = [self.op_path, "item", "list", "--vault", vault, "--format", "json"]

            # Set up environment with session token
            env = os.environ.copy()
            env["OP_SESSION_TOKEN"] = self.session_token

            # Execute the command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"Failed to list credentials: {stderr.decode()}")
                return False

            items = json.loads(stdout.decode())

            # Check if the item exists in the list
            for item in items:
                if item.get("title") == item_name:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking credential existence: {str(e)}")
            return False

    async def list_available_credentials(
        self, vault: str = None, category: str = None
    ) -> List[Dict[str, Any]]:
        """
        List available credentials in 1Password.

        Args:
            vault: The vault to use (default: self.default_vault)
            category: Filter by category (e.g., "API Credential")

        Returns:
            List of credential metadata (never includes actual secrets)
        """
        if not self.authenticated:
            logger.error("Not authenticated with 1Password")
            return []

        vault = vault or self.default_vault

        try:
            # Build the command to list items
            cmd = [self.op_path, "item", "list", "--vault", vault, "--format", "json"]
            if category:
                cmd.extend(["--categories", category])

            # Set up environment with session token
            env = os.environ.copy()
            env["OP_SESSION_TOKEN"] = self.session_token

            # Execute the command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"Failed to list credentials: {stderr.decode()}")
                return []

            items = json.loads(stdout.decode())

            # Return safe metadata (never include secrets)
            safe_items = []
            for item in items:
                safe_items.append(
                    {
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "category": item.get("category"),
                        "updated_at": item.get("updated_at"),
                        "created_at": item.get("created_at"),
                        "vault": item.get("vault", {}).get("name"),
                    }
                )

            return safe_items

        except Exception as e:
            logger.error(f"Error listing credentials: {str(e)}")
            return []

    async def inject_credentials_to_env(
        self, item_names: List[str], vault: str = None, env_map: Dict[str, str] = None
    ) -> Dict[str, str]:
        """
        Inject credentials into environment variables.

        Args:
            item_names: Names of the items to inject
            vault: The vault to use (default: self.default_vault)
            env_map: Mapping of item.field to env var name

        Returns:
            Dictionary of environment variables (without values for security)
        """
        if not self.authenticated:
            logger.error("Not authenticated with 1Password")
            return {}

        vault = vault or self.default_vault
        env_map = env_map or {}

        injected_vars = {}

        for item_name in item_names:
            try:
                # Get the item with all fields
                credential = await self.get_credential(item_name, vault=vault)

                if not credential:
                    logger.warning(
                        f"Could not inject credential '{item_name}': Not found"
                    )
                    continue

                # Apply mapping if specified, otherwise use default
                if item_name in env_map:
                    env_var = env_map[item_name]
                    os.environ[env_var] = credential
                    injected_vars[env_var] = "[REDACTED]"
                else:
                    # Default naming: ITEM_NAME_PASSWORD (uppercase, spaces to underscores)
                    env_var = f"{item_name.upper().replace(' ', '_')}_PASSWORD"
                    os.environ[env_var] = credential
                    injected_vars[env_var] = "[REDACTED]"

                logger.info(
                    f"Injected credential '{item_name}' into environment variable"
                )

            except Exception as e:
                logger.error(f"Error injecting credential '{item_name}': {str(e)}")

        return injected_vars

    def _find_op_executable(self) -> Optional[str]:
        """
        Find the 1Password CLI executable (op) in the system PATH.

        Returns:
            Path to the executable, or None if not found
        """
        # Try common executable names
        for executable in ["op", "op.exe"]:
            try:
                # Use 'which' on Unix-like systems or 'where' on Windows
                if os.name == "nt":  # Windows
                    result = subprocess.run(
                        ["where", executable], capture_output=True, text=True
                    )
                else:  # Unix-like
                    result = subprocess.run(
                        ["which", executable], capture_output=True, text=True
                    )

                if result.returncode == 0:
                    path = result.stdout.strip()
                    logger.info(f"Found 1Password CLI at: {path}")
                    return path
            except Exception:
                pass

        logger.warning("1Password CLI (op) not found in PATH")
        return None
