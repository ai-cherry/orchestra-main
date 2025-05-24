"""
Portkey Management API Client.

This module provides a client for interacting with the Portkey Management API
to programmatically manage virtual keys, gateway configurations, and other Portkey resources.

Security Note:
This module requires access to the MASTER_PORTKEY_ADMIN_KEY, which has administrative
privileges. Ensure this key is stored securely and access to these functions is
properly controlled and audited.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logger = logging.getLogger(__name__)

# Base URL for Portkey Management API
PORTKEY_API_BASE_URL = "https://api.portkey.ai/v1"


class PortkeyAdminException(Exception):
    """Exception raised for errors in the Portkey Admin client."""


@dataclass
class VirtualKey:
    """Data class representing a Portkey Virtual Key."""

    id: str
    name: str
    provider: str
    created_at: str
    last_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    usage_stats: Optional[Dict[str, Any]] = None


@dataclass
class GatewayConfig:
    """Data class representing a Portkey Gateway Configuration."""

    id: str
    name: str
    routing_strategy: str
    provider_configs: List[Dict[str, Any]]
    cache_config: Optional[Dict[str, Any]] = None
    created_at: str = None
    updated_at: str = None


class PortkeyAdminClient:
    """
    Client for the Portkey Management API.

    This client provides methods to programmatically manage Portkey resources including:
    - Virtual Keys for different providers (OpenAI, Anthropic, etc.)
    - Gateway Configurations for routing strategies
    - Usage statistics and budget controls
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Portkey Admin client.

        Args:
            api_key: Portkey Admin API key. If not provided, will attempt to read from
                     the MASTER_PORTKEY_ADMIN_KEY environment variable.

        Raises:
            PortkeyAdminException: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.environ.get("MASTER_PORTKEY_ADMIN_KEY")

        if not self.api_key:
            raise PortkeyAdminException(
                "No Portkey Admin API key provided. Please provide an API key or "
                "set the MASTER_PORTKEY_ADMIN_KEY environment variable."
            )

        # Set up session with authorization header
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and errors.

        Args:
            response: The API response to handle

        Returns:
            The JSON response data

        Raises:
            PortkeyAdminException: If the API request failed
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            error_msg = f"Portkey API request failed: {e}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"{error_msg} - {error_data['error']}"
            except ValueError:
                pass

            logger.error(error_msg)
            raise PortkeyAdminException(error_msg) from e
        except ValueError:
            error_msg = "Invalid JSON response from Portkey API"
            logger.error(error_msg)
            raise PortkeyAdminException(error_msg)

    # Virtual Key Management

    def create_virtual_key(
        self,
        name: str,
        provider_key: str,
        provider: str,
        description: Optional[str] = None,
        budget_limit: Optional[float] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VirtualKey:
        """
        Create a new Virtual Key in Portkey.

        Args:
            name: Name for the virtual key
            provider_key: The actual API key for the provider
            provider: Provider name (e.g., 'openai', 'anthropic', 'mistral')
            description: Optional description for the key
            budget_limit: Optional monthly budget limit in USD
            rate_limit: Optional rate limit (requests per minute)
            metadata: Optional metadata for the key

        Returns:
            A VirtualKey object with the created key's details

        Raises:
            PortkeyAdminException: If the API request failed
        """
        payload = {"name": name, "provider": provider, "provider_key": provider_key}

        if description:
            payload["description"] = description
        if budget_limit is not None:
            payload["budget_limit"] = budget_limit
        if rate_limit is not None:
            payload["rate_limit"] = rate_limit
        if metadata:
            payload["metadata"] = metadata

        url = f"{PORTKEY_API_BASE_URL}/virtual-keys"
        response = self.session.post(url, json=payload)
        data = self._handle_response(response)

        logger.info(f"Created new virtual key: {name} for provider: {provider}")
        return VirtualKey(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            created_at=data["created_at"],
            metadata=data.get("metadata"),
        )

    def list_virtual_keys(self, provider: Optional[str] = None) -> List[VirtualKey]:
        """
        List existing Virtual Keys.

        Args:
            provider: Optional filter by provider

        Returns:
            List of VirtualKey objects

        Raises:
            PortkeyAdminException: If the API request failed
        """
        url = f"{PORTKEY_API_BASE_URL}/virtual-keys"
        if provider:
            url += f"?provider={provider}"

        response = self.session.get(url)
        data = self._handle_response(response)

        keys = []
        for item in data.get("virtual_keys", []):
            keys.append(
                VirtualKey(
                    id=item["id"],
                    name=item["name"],
                    provider=item["provider"],
                    created_at=item["created_at"],
                    last_used=item.get("last_used"),
                    metadata=item.get("metadata"),
                    usage_stats=item.get("usage_stats"),
                )
            )

        return keys

    def get_virtual_key(self, key_id: str) -> VirtualKey:
        """
        Get details of a specific Virtual Key.

        Args:
            key_id: ID of the virtual key

        Returns:
            VirtualKey object with the key's details

        Raises:
            PortkeyAdminException: If the API request failed or key not found
        """
        url = f"{PORTKEY_API_BASE_URL}/virtual-keys/{key_id}"
        response = self.session.get(url)
        data = self._handle_response(response)

        return VirtualKey(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            created_at=data["created_at"],
            last_used=data.get("last_used"),
            metadata=data.get("metadata"),
            usage_stats=data.get("usage_stats"),
        )

    def update_virtual_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        budget_limit: Optional[float] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VirtualKey:
        """
        Update a Virtual Key.

        Args:
            key_id: ID of the virtual key to update
            name: Optional new name for the key
            description: Optional new description
            budget_limit: Optional new budget limit
            rate_limit: Optional new rate limit
            metadata: Optional new metadata

        Returns:
            Updated VirtualKey object

        Raises:
            PortkeyAdminException: If the API request failed or key not found
        """
        payload = {}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if budget_limit is not None:
            payload["budget_limit"] = budget_limit
        if rate_limit is not None:
            payload["rate_limit"] = rate_limit
        if metadata:
            payload["metadata"] = metadata

        if not payload:
            logger.warning("No update parameters provided for virtual key update")
            return self.get_virtual_key(key_id)

        url = f"{PORTKEY_API_BASE_URL}/virtual-keys/{key_id}"
        response = self.session.patch(url, json=payload)
        data = self._handle_response(response)

        logger.info(f"Updated virtual key: {key_id}")
        return VirtualKey(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            created_at=data["created_at"],
            metadata=data.get("metadata"),
        )

    def delete_virtual_key(self, key_id: str) -> bool:
        """
        Delete a Virtual Key.

        Args:
            key_id: ID of the virtual key to delete

        Returns:
            True if deletion was successful

        Raises:
            PortkeyAdminException: If the API request failed or key not found
        """
        url = f"{PORTKEY_API_BASE_URL}/virtual-keys/{key_id}"
        response = self.session.delete(url)
        self._handle_response(response)

        logger.info(f"Deleted virtual key: {key_id}")
        return True

    def rotate_virtual_key(self, key_id: str, new_provider_key: str) -> VirtualKey:
        """
        Rotate a Virtual Key by updating the provider key.

        Args:
            key_id: ID of the virtual key to rotate
            new_provider_key: New provider API key

        Returns:
            Updated VirtualKey object

        Raises:
            PortkeyAdminException: If the API request failed or key not found
        """
        url = f"{PORTKEY_API_BASE_URL}/virtual-keys/{key_id}/rotate"
        payload = {"provider_key": new_provider_key}

        response = self.session.post(url, json=payload)
        data = self._handle_response(response)

        logger.info(f"Rotated virtual key: {key_id}")
        return VirtualKey(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            created_at=data["created_at"],
            metadata=data.get("metadata"),
        )

    # Gateway Configuration Management

    def create_gateway_config(
        self,
        name: str,
        routing_strategy: str,
        provider_configs: List[Dict[str, Any]],
        cache_config: Optional[Dict[str, Any]] = None,
    ) -> GatewayConfig:
        """
        Create a new Gateway Configuration.

        Args:
            name: Name for the gateway configuration
            routing_strategy: Routing strategy (e.g., 'fallback', 'loadbalance', 'cost_aware')
            provider_configs: List of provider configurations
            cache_config: Optional cache configuration

        Returns:
            GatewayConfig object with the created configuration's details

        Raises:
            PortkeyAdminException: If the API request failed
        """
        payload = {
            "name": name,
            "routing_strategy": routing_strategy,
            "provider_configs": provider_configs,
        }

        if cache_config:
            payload["cache_config"] = cache_config

        url = f"{PORTKEY_API_BASE_URL}/gateway-configs"
        response = self.session.post(url, json=payload)
        data = self._handle_response(response)

        logger.info(f"Created new gateway config: {name} with strategy: {routing_strategy}")
        return GatewayConfig(
            id=data["id"],
            name=data["name"],
            routing_strategy=data["routing_strategy"],
            provider_configs=data["provider_configs"],
            cache_config=data.get("cache_config"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def list_gateway_configs(self) -> List[GatewayConfig]:
        """
        List existing Gateway Configurations.

        Returns:
            List of GatewayConfig objects

        Raises:
            PortkeyAdminException: If the API request failed
        """
        url = f"{PORTKEY_API_BASE_URL}/gateway-configs"
        response = self.session.get(url)
        data = self._handle_response(response)

        configs = []
        for item in data.get("gateway_configs", []):
            configs.append(
                GatewayConfig(
                    id=item["id"],
                    name=item["name"],
                    routing_strategy=item["routing_strategy"],
                    provider_configs=item["provider_configs"],
                    cache_config=item.get("cache_config"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                )
            )

        return configs

    def get_gateway_config(self, config_id: str) -> GatewayConfig:
        """
        Get details of a specific Gateway Configuration.

        Args:
            config_id: ID of the gateway configuration

        Returns:
            GatewayConfig object with the configuration's details

        Raises:
            PortkeyAdminException: If the API request failed or config not found
        """
        url = f"{PORTKEY_API_BASE_URL}/gateway-configs/{config_id}"
        response = self.session.get(url)
        data = self._handle_response(response)

        return GatewayConfig(
            id=data["id"],
            name=data["name"],
            routing_strategy=data["routing_strategy"],
            provider_configs=data["provider_configs"],
            cache_config=data.get("cache_config"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update_gateway_config(
        self,
        config_id: str,
        name: Optional[str] = None,
        routing_strategy: Optional[str] = None,
        provider_configs: Optional[List[Dict[str, Any]]] = None,
        cache_config: Optional[Dict[str, Any]] = None,
    ) -> GatewayConfig:
        """
        Update a Gateway Configuration.

        Args:
            config_id: ID of the gateway configuration to update
            name: Optional new name
            routing_strategy: Optional new routing strategy
            provider_configs: Optional new provider configurations
            cache_config: Optional new cache configuration

        Returns:
            Updated GatewayConfig object

        Raises:
            PortkeyAdminException: If the API request failed or config not found
        """
        payload = {}
        if name:
            payload["name"] = name
        if routing_strategy:
            payload["routing_strategy"] = routing_strategy
        if provider_configs:
            payload["provider_configs"] = provider_configs
        if cache_config:
            payload["cache_config"] = cache_config

        if not payload:
            logger.warning("No update parameters provided for gateway config update")
            return self.get_gateway_config(config_id)

        url = f"{PORTKEY_API_BASE_URL}/gateway-configs/{config_id}"
        response = self.session.patch(url, json=payload)
        data = self._handle_response(response)

        logger.info(f"Updated gateway config: {config_id}")
        return GatewayConfig(
            id=data["id"],
            name=data["name"],
            routing_strategy=data["routing_strategy"],
            provider_configs=data["provider_configs"],
            cache_config=data.get("cache_config"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def delete_gateway_config(self, config_id: str) -> bool:
        """
        Delete a Gateway Configuration.

        Args:
            config_id: ID of the gateway configuration to delete

        Returns:
            True if deletion was successful

        Raises:
            PortkeyAdminException: If the API request failed or config not found
        """
        url = f"{PORTKEY_API_BASE_URL}/gateway-configs/{config_id}"
        response = self.session.delete(url)
        self._handle_response(response)

        logger.info(f"Deleted gateway config: {config_id}")
        return True

    # Usage Statistics

    def get_usage_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        virtual_key_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics for virtual keys.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            virtual_key_id: Optional filter by virtual key ID
            provider: Optional filter by provider

        Returns:
            Dictionary with usage statistics

        Raises:
            PortkeyAdminException: If the API request failed
        """
        url = f"{PORTKEY_API_BASE_URL}/usage"
        params = {}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if virtual_key_id:
            params["virtual_key_id"] = virtual_key_id
        if provider:
            params["provider"] = provider

        response = self.session.get(url, params=params)
        return self._handle_response(response)
