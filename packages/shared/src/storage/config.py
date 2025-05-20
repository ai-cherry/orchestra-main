"""
Enhanced storage configuration for the AI Orchestration System.

This module centralizes storage configuration settings, including collection
names, default settings, environment-based configuration, and data classification.
"""

import os
from typing import Dict, List, Any, Optional, Literal

# Default collection names
MEMORY_ITEMS_COLLECTION = "memory_items"
AGENT_DATA_COLLECTION = "agent_data"
USER_SESSIONS_COLLECTION = "user_sessions"
VECTOR_EMBEDDINGS_COLLECTION = "vector_embeddings"
DEV_NOTES_COLLECTION = "dev_notes"

# Data privacy classification levels
PrivacyLevel = Literal["standard", "sensitive", "critical"]

# Environment-based overrides
ENV_PREFIX = "ORCHESTRA_STORAGE_"


def get_collection_name(
    base_name: str,
    namespace: Optional[str] = None,
    privacy_level: Optional[PrivacyLevel] = None,
    environment: Optional[str] = None,
) -> str:
    """
    Get a collection name with appropriate namespacing and classification.

    Args:
        base_name: Base collection name
        namespace: Optional namespace to prefix (for multi-tenant deployments)
        privacy_level: Optional privacy classification level
        environment: Optional environment name (dev, staging, prod)

    Returns:
        Collection name, potentially with namespace and/or environment overrides
    """
    # Check for environment override
    env_override = os.environ.get(f"{ENV_PREFIX}{base_name.upper()}")
    if env_override:
        base_name = env_override

    # Start with base name
    result = base_name

    # Add privacy level suffix if provided
    if privacy_level:
        result = f"{result}_{privacy_level}"

    # Add environment suffix if provided
    if environment:
        result = f"{result}_{environment}"

    # Add namespace prefix if provided (goes at the very start)
    if namespace:
        result = f"{namespace}_{result}"

    return result


class StorageConfig:
    """
    Enhanced storage configuration class for centralizing settings
    and enforcing data classification policies.
    """

    def __init__(
        self,
        namespace: Optional[str] = None,
        environment: Optional[str] = None,
        collection_overrides: Optional[Dict[str, str]] = None,
        default_privacy_level: PrivacyLevel = "standard",
        enforce_privacy_classification: bool = False,
        enable_dev_notes: bool = True,
    ):
        """
        Initialize storage configuration.

        Args:
            namespace: Optional namespace for multi-tenant deployments
            environment: Optional environment name (dev, staging, prod)
            collection_overrides: Optional mapping of collection names to override
            default_privacy_level: Default privacy level for collections
            enforce_privacy_classification: Whether to enforce privacy classification
            enable_dev_notes: Whether to enable development notes collection
        """
        self.namespace = namespace
        self.environment = environment
        self.collection_overrides = collection_overrides or {}
        self.default_privacy_level = default_privacy_level
        self.enforce_privacy_classification = enforce_privacy_classification
        self.enable_dev_notes = enable_dev_notes

    def get_collection_name(
        self, base_name: str, privacy_level: Optional[PrivacyLevel] = None
    ) -> str:
        """
        Get a collection name with all configuration applied.

        Args:
            base_name: Base collection name
            privacy_level: Optional privacy classification level

        Returns:
            Final collection name with overrides, namespace, and classification applied
        """
        # Apply override if present
        name = self.collection_overrides.get(base_name, base_name)

        # Get final privacy level
        final_privacy_level = (
            privacy_level if privacy_level else self.default_privacy_level
        )

        # Apply namespace, privacy level, and environment
        return get_collection_name(
            name,
            namespace=self.namespace,
            privacy_level=final_privacy_level,
            environment=self.environment,
        )

    def get_dev_notes_collection(self) -> str:
        """
        Get the development notes collection name.

        Returns:
            Collection name for development notes

        Raises:
            RuntimeError: If dev notes are disabled
        """
        if not self.enable_dev_notes:
            raise RuntimeError("Development notes are disabled in this configuration")

        return self.get_collection_name(DEV_NOTES_COLLECTION)

    def with_namespace(self, namespace: str) -> "StorageConfig":
        """
        Create a new configuration with an updated namespace.

        Args:
            namespace: The namespace to use

        Returns:
            A new StorageConfig instance with the updated namespace
        """
        return StorageConfig(
            namespace=namespace,
            environment=self.environment,
            collection_overrides=self.collection_overrides.copy(),
            default_privacy_level=self.default_privacy_level,
            enforce_privacy_classification=self.enforce_privacy_classification,
            enable_dev_notes=self.enable_dev_notes,
        )

    def with_environment(self, environment: str) -> "StorageConfig":
        """
        Create a new configuration with an updated environment.

        Args:
            environment: The environment to use

        Returns:
            A new StorageConfig instance with the updated environment
        """
        return StorageConfig(
            namespace=self.namespace,
            environment=environment,
            collection_overrides=self.collection_overrides.copy(),
            default_privacy_level=self.default_privacy_level,
            enforce_privacy_classification=self.enforce_privacy_classification,
            enable_dev_notes=self.enable_dev_notes,
        )
