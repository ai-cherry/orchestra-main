"""
Base deployment abstractions for Orchestra AI infrastructure.

This module provides cloud-agnostic interfaces for deployment operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from pulumi import Output


class DeploymentEnvironment(Enum):
    """Deployment environment types."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ResourceSize(Enum):
    """Standard resource sizes."""

    SMALL = "small"  # 1 vCPU, 2GB RAM
    MEDIUM = "medium"  # 2 vCPU, 4GB RAM
    LARGE = "large"  # 4 vCPU, 8GB RAM
    XLARGE = "xlarge"  # 8 vCPU, 16GB RAM


@dataclass
class DeploymentConfig:
    """Configuration for a deployment."""

    environment: DeploymentEnvironment
    project_name: str
    region: str
    resource_size: ResourceSize = ResourceSize.MEDIUM
    enable_monitoring: bool = True
    enable_backups: bool = False
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {
                "project": self.project_name,
                "environment": self.environment.value,
                "managed-by": "pulumi",
            }


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""

    def __init__(self, config: DeploymentConfig):
        self.config = config

    @abstractmethod
    def create_compute_instance(
        self, name: str, image: str, user_data: Optional[str] = None
    ) -> Output[str]:
        """Create a compute instance and return its IP address."""
        pass

    @abstractmethod
    def create_managed_database(
        self, name: str, engine: str, version: str
    ) -> Output[Dict[str, Any]]:
        """Create a managed database and return connection info."""
        pass

    @abstractmethod
    def create_object_storage(self, name: str, public: bool = False) -> Output[str]:
        """Create object storage and return its URL."""
        pass

    @abstractmethod
    def create_firewall_rules(self, name: str, rules: List[Dict[str, Any]]) -> Any:
        """Create firewall rules for security."""
        pass


class DeploymentOrchestrator:
    """Orchestrates deployments across different cloud providers."""

    def __init__(self, provider: CloudProvider):
        self.provider = provider
        self.resources = {}

    def deploy_orchestra_stack(self) -> Dict[str, Output[Any]]:
        """Deploy the complete Orchestra AI stack."""
        outputs = {}

        # Deploy compute resources
        outputs["api_server_ip"] = self.provider.create_compute_instance(
            name=f"orchestra-api-{self.provider.config.environment.value}",
            image="ubuntu-22-04-x64",
            user_data=self._generate_api_server_script(),
        )

        # Deploy firewall rules
        self.provider.create_firewall_rules(
            name=f"orchestra-firewall-{self.provider.config.environment.value}",
            rules=[
                {"protocol": "tcp", "port": 22, "source": "0.0.0.0/0"},
                {"protocol": "tcp", "port": 80, "source": "0.0.0.0/0"},
                {"protocol": "tcp", "port": 443, "source": "0.0.0.0/0"},
                {"protocol": "tcp", "port": 8080, "source": "0.0.0.0/0"},
            ],
        )

        return outputs

    def _generate_api_server_script(self) -> str:
        """Generate cloud-init script for API server."""
        return """#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Python 3.10
apt-get install -y python3.10 python3.10-venv python3-pip

# Create app directory
mkdir -p /opt/orchestra-ai
cd /opt/orchestra-ai

# Install docker-compose
pip3 install docker-compose

# Start services
echo "Orchestra AI infrastructure ready"
"""
