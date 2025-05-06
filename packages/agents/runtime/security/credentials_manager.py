"""
Credentials Manager for Orchestra.

This module provides centralized credential management capabilities for the Orchestra system,
allowing agents and services to securely access and handle sensitive credentials while
maintaining security best practices.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
import json

from packages.agents.base import BaseAgent

# Import from future directory since OnePasswordAgent has been moved
from future.packages.agents.runtime.security.onepassword_agent import OnePasswordAgent

logger = logging.getLogger(__name__)


class CredentialsManager(BaseAgent):
    """
    Agent responsible for securely managing credentials across the Orchestra platform.

    This agent serves as a central hub for credential management, integrating with
    various secure credential stores (like 1Password) and providing a unified interface
    for obtaining and managing credentials without exposing sensitive information.
    """

    def __init__(
        self,
        agent_id: str = "credentials-manager",
        name: str = "Credentials Manager",
        description: str = "Manages secure access to credentials across the Orchestra platform",
        config: Dict[str, Any] = None,
        persona: Dict[str, Any] = None,
    ):
        """
        Initialize the Credentials Manager.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of agent's purpose
            config: Agent-specific configuration
            persona: Optional persona configuration
        """
        # Create config dictionary if not provided
        if config is None:
            config = {
                "id": agent_id,
                "name": name,
                "description": description
            }
        
        super().__init__(config=config, persona=persona)
        self.providers = {}
        self.default_provider = None

        # Will be populated during initialization
        self.onepassword_agent = None

    async def initialize(self) -> None:
        """Initialize the agent and set up credential providers."""
        # Set up 1Password integration if configured
        op_service_token = os.environ.get("OP_SERVICE_ACCOUNT_TOKEN")
        if op_service_token:
            try:
                self.onepassword_agent = OnePasswordAgent(
                    service_account_token=op_service_token
                )
                await self.onepassword_agent.initialize()

                if self.onepassword_agent.authenticated:
                    self.providers["1password"] = self.onepassword_agent
                    self.default_provider = "1password"
                    logger.info(
                        "1Password credential provider initialized successfully"
                    )
                else:
                    logger.warning(
                        "1Password authentication failed, provider not registered"
                    )
            except Exception as e:
                logger.error(f"Failed to initialize 1Password provider: {str(e)}")
        else:
            logger.info(
                "1Password service token not found in environment, provider not registered"
            )

        # Could add other credential providers here (AWS Secrets Manager, HashiCorp Vault, etc.)

        if not self.providers:
            logger.warning("No credential providers were initialized")
        else:
            logger.info(
                f"Credentials Manager initialized with providers: {', '.join(self.providers.keys())}"
            )

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a credential access request.

        Args:
            context: Dictionary containing:
                - request_type: Type of credential request
                - provider: (Optional) Provider to use
                - credential_name: (Optional) Name of the credential
                - vault: (Optional) Vault or collection
                - category: (Optional) Category filter

        Returns:
            Dictionary containing the request result
        """
        # Extract request details
        request_type = context.get("request_type", "unknown")
        provider = context.get("provider", self.default_provider)
        input_text = context.get("input_text", "")

        if not self.providers:
            return {
                "status": "error",
                "message": "No credential providers are configured."
            }

        if provider not in self.providers:
            available_providers = ", ".join(self.providers.keys())
            return {
                "status": "error",
                "message": f"Unknown credential provider '{provider}'. Available providers: {available_providers}"
            }

        # Delegate to the appropriate provider
        if request_type == "get_credential":
            # This should never return the actual credential in the response
            credential_name = context.get("credential_name")

            if not credential_name:
                return {
                    "status": "error",
                    "message": "No credential name provided."
                }

            # Instead of returning credential, confirm access and store
            # in a secure context that only authorized agents can access
            return {
                "status": "success",
                "message": f"Credential '{credential_name}' would be securely accessed through {provider}."
            }

        elif request_type == "check_exists":
            credential_name = context.get("credential_name")

            if not credential_name:
                return {
                    "status": "error",
                    "message": "No credential name provided."
                }

            result = await self.check_credential_exists(
                credential_name, provider=provider, vault=context.get("vault")
            )

            return {
                "status": "success",
                "exists": result,
                "message": f"Credential '{credential_name}' {'exists' if result else 'does not exist'} in provider '{provider}'."
            }

        elif request_type == "list_available":
            result = await self.list_available_credentials(
                provider=provider,
                vault=context.get("vault"),
                category=context.get("category"),
            )

            if not result:
                return {
                    "status": "success",
                    "count": 0,
                    "credentials": [],
                    "message": f"No credentials found in provider '{provider}'."
                }

            return {
                "status": "success",
                "count": len(result),
                "credentials": result,
                "message": f"Found {len(result)} credentials in provider '{provider}'."
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown request type '{request_type}'. Valid types are: get_credential, check_exists, list_available."
            }

    async def get_credential(
        self,
        credential_name: str,
        provider: str = None,
        vault: str = None,
        field: str = None,
    ) -> Optional[str]:
        """
        Get a credential from the specified provider.

        Args:
            credential_name: The name of the credential
            provider: The provider to use (default: self.default_provider)
            vault: The vault or collection within the provider
            field: The specific field to retrieve

        Returns:
            The credential value, or None if it could not be retrieved

        Note:
            This method returns the actual credential and should NEVER be
            directly exposed through an API or response. It should only
            be used internally by trusted agents.
        """
        provider = provider or self.default_provider

        if not provider or provider not in self.providers:
            logger.error(f"Unknown credential provider: {provider}")
            return None

        provider_agent = self.providers[provider]

        if provider == "1password":
            return await provider_agent.get_credential(
                credential_name, field=field, vault=vault
            )

        # Add handlers for other providers as needed

        return None

    async def check_credential_exists(
        self, credential_name: str, provider: str = None, vault: str = None
    ) -> bool:
        """
        Check if a credential exists in the specified provider.

        Args:
            credential_name: The name of the credential
            provider: The provider to use (default: self.default_provider)
            vault: The vault or collection within the provider

        Returns:
            True if the credential exists, False otherwise
        """
        provider = provider or self.default_provider

        if not provider or provider not in self.providers:
            logger.error(f"Unknown credential provider: {provider}")
            return False

        provider_agent = self.providers[provider]

        if provider == "1password":
            return await provider_agent.check_credential_exists(
                credential_name, vault=vault
            )

        # Add handlers for other providers as needed

        return False

    async def list_available_credentials(
        self, provider: str = None, vault: str = None, category: str = None
    ) -> List[Dict[str, Any]]:
        """
        List available credentials in the specified provider.

        Args:
            provider: The provider to use (default: self.default_provider)
            vault: The vault or collection within the provider
            category: Filter by category

        Returns:
            List of credential metadata (never includes actual secrets)
        """
        provider = provider or self.default_provider

        if not provider or provider not in self.providers:
            logger.error(f"Unknown credential provider: {provider}")
            return []

        provider_agent = self.providers[provider]

        if provider == "1password":
            return await provider_agent.list_available_credentials(
                vault=vault, category=category
            )

        # Add handlers for other providers as needed

        return []

    async def inject_credentials_to_env(
        self,
        credential_names: List[str],
        provider: str = None,
        vault: str = None,
        env_map: Dict[str, str] = None,
    ) -> Dict[str, str]:
        """
        Inject credentials into environment variables.

        Args:
            credential_names: Names of the credentials to inject
            provider: The provider to use (default: self.default_provider)
            vault: The vault or collection within the provider
            env_map: Mapping of credential names to env var names

        Returns:
            Dictionary of environment variables (without values for security)
        """
        provider = provider or self.default_provider

        if not provider or provider not in self.providers:
            logger.error(f"Unknown credential provider: {provider}")
            return {}

        provider_agent = self.providers[provider]

        if provider == "1password":
            return await provider_agent.inject_credentials_to_env(
                credential_names, vault=vault, env_map=env_map
            )

        # Add handlers for other providers as needed

        return {}

    async def provision_credentials_for_agent(
        self, agent_id: str, credential_mapping: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Provision credentials for a specific agent.

        Args:
            agent_id: ID of the agent that needs credentials
            credential_mapping: Mapping of agent credential needs to provider credentials
                Format: {
                    "env_var_name": {
                        "provider": "provider_name",
                        "credential_name": "name_in_provider",
                        "vault": "optional_vault_name",
                        "field": "optional_field_name"
                    },
                    ...
                }

        Returns:
            True if all credentials were successfully provisioned, False otherwise
        """
        if not credential_mapping:
            logger.warning(f"No credential mapping provided for agent {agent_id}")
            return False

        success = True
        env_map = {}

        # Group credentials by provider for efficiency
        by_provider = {}
        for env_var, details in credential_mapping.items():
            provider = details.get("provider", self.default_provider)

            if not provider or provider not in self.providers:
                logger.error(f"Unknown credential provider: {provider}")
                success = False
                continue

            if provider not in by_provider:
                by_provider[provider] = {}

            by_provider[provider][details["credential_name"]] = env_var

        # Process each provider
        for provider, credentials in by_provider.items():
            provider_agent = self.providers[provider]

            if provider == "1password":
                result = await provider_agent.inject_credentials_to_env(
                    list(credentials.keys()),
                    vault=next(iter(credential_mapping.values())).get("vault"),
                    env_map=credentials,
                )

                if not result:
                    success = False

            # Add handlers for other providers as needed

        return success

    def process_feedback(self, feedback: Dict[str, Any]) -> None:
        """Process feedback about the agent's performance."""
        logger.info(f"Credentials Manager received feedback: {feedback}")
        super().process_feedback(feedback)
    
    def shutdown(self) -> None:
        """Perform any necessary cleanup when shutting down the agent."""
        logger.info(f"Shutting down Credentials Manager")
        super().shutdown()


# Global credential manager instance
_credentials_manager = None


def get_credentials_manager() -> CredentialsManager:
    """
    Get the global credentials manager instance.

    Returns:
        The global CredentialsManager instance
    """
    global _credentials_manager

    if _credentials_manager is None:
        _credentials_manager = CredentialsManager()

    return _credentials_manager
