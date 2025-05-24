"""
Model version management for AI Orchestra.

This module provides tools for managing model versions and deployments,
enabling blue/green deployment and traffic shifting.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ai_orchestra.core.interfaces.ai_service import AIService
from ai_orchestra.core.interfaces.memory import MemoryProvider

logger = logging.getLogger(__name__)


class ModelVersion:
    """Model version information."""

    def __init__(
        self,
        model_id: str,
        version: str,
        endpoint: str,
        capabilities: List[str],
        created_at: float,
    ):
        """
        Initialize model version.

        Args:
            model_id: The model ID
            version: The version
            endpoint: The model endpoint
            capabilities: List of capabilities
            created_at: Creation timestamp
        """
        self.model_id = model_id
        self.version = version
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        """Create model version from dictionary."""
        return cls(
            model_id=data["model_id"],
            version=data["version"],
            endpoint=data["endpoint"],
            capabilities=data["capabilities"],
            created_at=data["created_at"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "version": self.version,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
        }


class DeploymentStrategy:
    """Model deployment strategy."""

    def __init__(
        self,
        model_id: str,
        version: str,
        traffic_percentage: int = 0,
    ):
        """
        Initialize deployment strategy.

        Args:
            model_id: The model ID
            version: The version
            traffic_percentage: Percentage of traffic to route to this version
        """
        self.model_id = model_id
        self.version = version
        self.traffic_percentage = traffic_percentage

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeploymentStrategy":
        """Create deployment strategy from dictionary."""
        return cls(
            model_id=data["model_id"],
            version=data["version"],
            traffic_percentage=data["traffic_percentage"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "version": self.version,
            "traffic_percentage": self.traffic_percentage,
        }


class ModelVersionManager:
    """Manager for model versions and deployments."""

    def __init__(
        self,
        memory_provider: MemoryProvider,
        ai_service: AIService,
    ):
        """
        Initialize the model version manager.

        Args:
            memory_provider: The memory provider to use
            ai_service: The AI service to use
        """
        self.memory_provider = memory_provider
        self.ai_service = ai_service

    def _get_model_key(self, model_id: str) -> str:
        """Get the key for model information."""
        return f"model:{model_id}"

    def _get_version_key(self, model_id: str, version: str) -> str:
        """Get the key for version information."""
        return f"model:{model_id}:version:{version}"

    def _get_deployment_key(self, model_id: str) -> str:
        """Get the key for deployment information."""
        return f"model:{model_id}:deployment"

    async def register_model_version(
        self,
        model_id: str,
        version: str,
        endpoint: str,
        capabilities: List[str],
    ) -> ModelVersion:
        """
        Register a new model version.

        Args:
            model_id: The model ID
            version: The version
            endpoint: The model endpoint
            capabilities: List of capabilities

        Returns:
            The registered model version
        """
        # Create model version
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            endpoint=endpoint,
            capabilities=capabilities,
            created_at=time.time(),
        )

        # Store model version
        version_key = self._get_version_key(model_id, version)
        await self.memory_provider.store(
            key=version_key,
            value=model_version.to_dict(),
        )

        # Update model versions list
        model_key = self._get_model_key(model_id)
        model_info = await self.memory_provider.retrieve(model_key) or {
            "model_id": model_id,
            "versions": [],
        }

        # Add version to list if not already present
        if version not in model_info["versions"]:
            model_info["versions"].append(version)

        # Store updated model information
        await self.memory_provider.store(
            key=model_key,
            value=model_info,
        )

        return model_version

    async def get_model_version(
        self,
        model_id: str,
        version: str,
    ) -> Optional[ModelVersion]:
        """
        Get a model version.

        Args:
            model_id: The model ID
            version: The version

        Returns:
            The model version, or None if not found
        """
        version_key = self._get_version_key(model_id, version)
        version_info = await self.memory_provider.retrieve(version_key)

        if not version_info:
            return None

        return ModelVersion.from_dict(version_info)

    async def list_model_versions(
        self,
        model_id: str,
    ) -> List[ModelVersion]:
        """
        List versions for a model.

        Args:
            model_id: The model ID

        Returns:
            List of model versions
        """
        model_key = self._get_model_key(model_id)
        model_info = await self.memory_provider.retrieve(model_key)

        if not model_info:
            return []

        versions = []
        for version in model_info["versions"]:
            version_info = await self.get_model_version(model_id, version)
            if version_info:
                versions.append(version_info)

        return versions

    async def update_deployment_strategy(
        self,
        model_id: str,
        strategies: List[DeploymentStrategy],
    ) -> bool:
        """
        Update deployment strategy for a model.

        Args:
            model_id: The model ID
            strategies: List of deployment strategies

        Returns:
            True if the deployment was updated, False otherwise
        """
        # Validate total traffic percentage
        total_percentage = sum(s.traffic_percentage for s in strategies)
        if total_percentage != 100:
            raise ValueError(f"Total traffic percentage must be 100, got {total_percentage}")

        # Validate versions exist
        for strategy in strategies:
            version = await self.get_model_version(model_id, strategy.version)
            if not version:
                raise ValueError(f"Version {strategy.version} not found for model {model_id}")

        # Store deployment strategy
        deployment_key = self._get_deployment_key(model_id)
        deployment_info = {
            "model_id": model_id,
            "strategies": [s.to_dict() for s in strategies],
            "updated_at": time.time(),
        }

        await self.memory_provider.store(
            key=deployment_key,
            value=deployment_info,
        )

        return True

    async def get_deployment_strategy(
        self,
        model_id: str,
    ) -> List[DeploymentStrategy]:
        """
        Get deployment strategy for a model.

        Args:
            model_id: The model ID

        Returns:
            List of deployment strategies
        """
        deployment_key = self._get_deployment_key(model_id)
        deployment_info = await self.memory_provider.retrieve(deployment_key)

        if not deployment_info:
            # Default to latest version if no deployment strategy
            versions = await self.list_model_versions(model_id)
            if not versions:
                return []

            latest_version = max(versions, key=lambda v: v.created_at)
            return [
                DeploymentStrategy(
                    model_id=model_id,
                    version=latest_version.version,
                    traffic_percentage=100,
                )
            ]

        return [DeploymentStrategy.from_dict(s) for s in deployment_info["strategies"]]

    async def select_model_version(
        self,
        model_id: str,
    ) -> Optional[ModelVersion]:
        """
        Select a model version based on deployment strategy.

        Args:
            model_id: The model ID

        Returns:
            The selected model version, or None if not found
        """
        strategies = await self.get_deployment_strategy(model_id)

        if not strategies:
            return None

        # Simple weighted random selection
        import random

        r = random.randint(1, 100)

        cumulative = 0
        for strategy in strategies:
            cumulative += strategy.traffic_percentage
            if r <= cumulative:
                return await self.get_model_version(model_id, strategy.version)

        # Fallback to first strategy
        return await self.get_model_version(model_id, strategies[0].version)

    async def create_blue_green_deployment(
        self,
        model_id: str,
        blue_version: str,
        green_version: str,
        green_traffic_percentage: int = 0,
    ) -> bool:
        """
        Create a blue/green deployment.

        Args:
            model_id: The model ID
            blue_version: The current stable version
            green_version: The new version to deploy
            green_traffic_percentage: Percentage of traffic to route to the green version

        Returns:
            True if the deployment was created, False otherwise
        """
        # Validate versions exist
        blue_model = await self.get_model_version(model_id, blue_version)
        if not blue_model:
            raise ValueError(f"Blue version {blue_version} not found for model {model_id}")

        green_model = await self.get_model_version(model_id, green_version)
        if not green_model:
            raise ValueError(f"Green version {green_version} not found for model {model_id}")

        # Validate traffic percentage
        if not 0 <= green_traffic_percentage <= 100:
            raise ValueError(f"Green traffic percentage must be between 0 and 100, got {green_traffic_percentage}")

        # Create deployment strategies
        strategies = [
            DeploymentStrategy(
                model_id=model_id,
                version=blue_version,
                traffic_percentage=100 - green_traffic_percentage,
            ),
            DeploymentStrategy(
                model_id=model_id,
                version=green_version,
                traffic_percentage=green_traffic_percentage,
            ),
        ]

        # Update deployment strategy
        return await self.update_deployment_strategy(model_id, strategies)

    async def shift_traffic(
        self,
        model_id: str,
        green_traffic_percentage: int,
    ) -> bool:
        """
        Shift traffic between blue and green versions.

        Args:
            model_id: The model ID
            green_traffic_percentage: Percentage of traffic to route to the green version

        Returns:
            True if traffic was shifted, False otherwise
        """
        # Get current deployment strategy
        strategies = await self.get_deployment_strategy(model_id)

        if len(strategies) != 2:
            raise ValueError(f"Expected 2 deployment strategies for blue/green deployment, got {len(strategies)}")

        # Sort strategies by traffic percentage (blue has more traffic initially)
        strategies.sort(key=lambda s: s.traffic_percentage, reverse=True)

        blue_strategy, green_strategy = strategies

        # Update traffic percentages
        blue_strategy.traffic_percentage = 100 - green_traffic_percentage
        green_strategy.traffic_percentage = green_traffic_percentage

        # Update deployment strategy
        return await self.update_deployment_strategy(model_id, [blue_strategy, green_strategy])

    async def promote_green_to_blue(
        self,
        model_id: str,
    ) -> bool:
        """
        Promote the green version to blue (make it the only version).

        Args:
            model_id: The model ID

        Returns:
            True if the green version was promoted, False otherwise
        """
        # Get current deployment strategy
        strategies = await self.get_deployment_strategy(model_id)

        if len(strategies) != 2:
            raise ValueError(f"Expected 2 deployment strategies for blue/green deployment, got {len(strategies)}")

        # Sort strategies by traffic percentage (blue has more traffic initially)
        strategies.sort(key=lambda s: s.traffic_percentage, reverse=True)

        # Promote green to blue (make it the only version)
        green_strategy = strategies[1]
        green_strategy.traffic_percentage = 100

        # Update deployment strategy
        return await self.update_deployment_strategy(model_id, [green_strategy])

    async def rollback_to_blue(
        self,
        model_id: str,
    ) -> bool:
        """
        Rollback to the blue version (make it the only version).

        Args:
            model_id: The model ID

        Returns:
            True if the rollback was successful, False otherwise
        """
        # Get current deployment strategy
        strategies = await self.get_deployment_strategy(model_id)

        if len(strategies) != 2:
            raise ValueError(f"Expected 2 deployment strategies for blue/green deployment, got {len(strategies)}")

        # Sort strategies by traffic percentage (blue has more traffic initially)
        strategies.sort(key=lambda s: s.traffic_percentage, reverse=True)

        # Rollback to blue (make it the only version)
        blue_strategy = strategies[0]
        blue_strategy.traffic_percentage = 100

        # Update deployment strategy
        return await self.update_deployment_strategy(model_id, [blue_strategy])
