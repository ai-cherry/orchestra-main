#!/usr/bin/env python3
"""
Simplified Hybrid Configuration for AI Orchestra

This module provides configuration management across environments
(local, Codespaces, Cloud Workstation, Cloud Run).
"""

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hybrid-config")


class Environment(Enum):
    """Application environment types."""

    LOCAL = "local"
    CODESPACES = "codespaces"
    WORKSTATION = "workstation"
    CLOUD_RUN = "cloud_run"

    @classmethod
    def detect(cls) -> "Environment":
        """Detect the current environment."""
        # Check Cloud Run
        if os.environ.get("K_SERVICE"):
            return cls.CLOUD_RUN

        # Check GitHub Codespaces
        if os.environ.get("CODESPACES") == "true":
            return cls.CODESPACES

        # Check GCP Cloud Workstation
        try:
            if os.path.exists("/google/workstations"):
                return cls.WORKSTATION
        except Exception:
            pass

        # Default to local
        return cls.LOCAL


class HybridConfig:
    """Configuration for hybrid environments."""

    def __init__(
        self, project_id: Optional[str] = None, config_path: Optional[str] = None
    ):
        """Initialize configuration."""
        # Set environment
        self.environment = Environment.detect()
        logger.info(f"Detected environment: {self.environment.value}")

        # Set project ID
        self.project_id = project_id or os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "cherry-ai-project"
        )

        # Set config path
        self.config_path = Path(config_path or "config")

        # Create config directory if needed
        os.makedirs(self.config_path, exist_ok=True)

        # Load config
        self.config = self._load_config()
        self.active_config = self._get_active_config()

        logger.info(f"Hybrid config initialized for {self.environment.value}")

    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """Load configuration from files."""
        config = {
            "local": {},
            "codespaces": {},
            "workstation": {},
            "cloud_run": {},
            "common": {},
        }

        for section in config:
            file_path = self.config_path / f"{section}.json"
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        config[section] = json.load(f)
                except Exception as e:
                    logger.warning(f"Error loading {file_path}: {e}")

        return config

    def _get_active_config(self) -> Dict[str, Any]:
        """Get active configuration."""
        # Start with common
        active = dict(self.config.get("common", {}))

        # Overlay environment-specific
        env_config = self.config.get(self.environment.value, {})
        active.update(env_config)

        return active

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.active_config.get(key, default)

    def get_endpoint(self, service_name: str) -> str:
        """Get service endpoint."""
        # Check for direct override
        endpoint_key = f"{service_name}_endpoint"
        if endpoint_key in self.active_config:
            return self.active_config[endpoint_key]

        # Check for endpoints in config
        endpoints = self.active_config.get("endpoints", {})
        if service_name in endpoints:
            return endpoints[service_name]

        # Generate based on environment
        if self.environment == Environment.CLOUD_RUN:
            return f"https://{service_name}-internal.{self.project_id}.cloud.goog"
        elif self.environment == Environment.WORKSTATION:
            return f"https://{service_name}.{self.project_id}.cloud.goog"
        else:
            # Local/Codespaces: use localhost with port
            service_index = {"admin-api": 0, "memory": 1, "agent": 2, "mcp": 3}.get(
                service_name, 10
            )
            return f"http://localhost:{8000 + service_index}"

    def get_connections(self) -> Dict[str, str]:
        """Get all service connections."""
        services = ["admin-api", "memory", "agent", "mcp"]
        return {service: self.get_endpoint(service) for service in services}

    def is_production(self) -> bool:
        """Check if production environment."""
        return self.environment == Environment.CLOUD_RUN

    def is_development(self) -> bool:
        """Check if development environment."""
        return self.environment != Environment.CLOUD_RUN

    def create_defaults(self) -> bool:
        """Create default config files."""
        try:
            # Common config
            common_path = self.config_path / "common.json"
            if not common_path.exists():
                with open(common_path, "w") as f:
                    json.dump({"project_id": self.project_id}, f, indent=2)

            # Environment configs
            env_files = {
                "local.json": {
                    "endpoints": {
                        "admin-api": "http://localhost:8000",
                        "memory": "http://localhost:8001",
                    }
                },
                "cloud_run.json": {"enable_monitoring": True},
            }

            for filename, data in env_files.items():
                file_path = self.config_path / filename
                if not file_path.exists():
                    with open(file_path, "w") as f:
                        json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error creating defaults: {e}")
            return False


# Default instance
_default_config = None


def get_config(
    project_id: Optional[str] = None,
    config_path: Optional[str] = None,
    force_new: bool = False,
) -> HybridConfig:
    """Get default config instance."""
    global _default_config

    if _default_config is None or force_new:
        _default_config = HybridConfig(project_id=project_id, config_path=config_path)

    return _default_config


if __name__ == "__main__":
    """CLI interface."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Hybrid Config")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--config", help="Config directory")
    parser.add_argument(
        "--create-defaults", action="store_true", help="Create default configs"
    )
    parser.add_argument("--key", help="Config key to get")
    parser.add_argument("--service", help="Service for endpoint")
    parser.add_argument("--list-all", action="store_true", help="List all connections")

    args = parser.parse_args()

    # Create config
    config = HybridConfig(project_id=args.project, config_path=args.config)

    # Show basic info
    print(f"Environment: {config.environment.value}")
    print(f"Project ID: {config.project_id}")
    print(f"Is Production: {config.is_production()}")

    # Create defaults if requested
    if args.create_defaults:
        if config.create_defaults():
            print("Default configs created")
        else:
            print("Failed to create defaults")
            sys.exit(1)

    # Get specific config
    if args.key:
        value = config.get(args.key)
        print(f"{args.key}: {value}")

    # Get service endpoint
    if args.service:
        endpoint = config.get_endpoint(args.service)
        print(f"{args.service} endpoint: {endpoint}")

    # List all connections
    if args.list_all:
        connections = config.get_connections()
        print("\nService Connections:")
        for service, endpoint in connections.items():
            print(f"  {service}: {endpoint}")
