"""
SuperAGI deployment configuration for DigitalOcean.
Manages containerized deployment with proper environment setup.
"""

from typing import Dict
import pulumi
from pulumi import Config
import pulumi_digitalocean as do
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SuperAGIDeployment:
    def __init__(self, name: str, config: Dict[str, str]):
        """
        Initialize SuperAGI deployment resources.

        Args:
            name: Deployment name prefix
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self._validate_config()
        self._deploy_container()

    def _validate_config(self) -> None:
        """Verify required configuration parameters."""
        required_keys = {"region", "db_url", "weaviate_url"}
        if not required_keys.issubset(self.config.keys()):
            missing = required_keys - set(self.config.keys())
            raise ValueError(f"Missing required config keys: {missing}")

    def _deploy_container(self) -> None:
        """Deploy SuperAGI container with proper configuration."""
        # Get container registry
        registry = do.ContainerRegistry(
            f"{self.name}-registry", subscription_tier_slug="basic"
        )

        # Configure container environment
        env_vars = [
            do.AppSpecEnvArgs(key="DB_URL", value=self.config["db_url"]),
            do.AppSpecEnvArgs(key="WEAVIATE_URL", value=self.config["weaviate_url"]),
            do.AppSpecEnvArgs(
                key="ENVIRONMENT", value=self.config.get("env", "production")
            ),
        ]

        # Create container app
        self.app = do.App(
            f"{self.name}-app",
            spec=do.AppSpecArgs(
                name="superagi",
                region=self.config["region"],
                services=[
                    do.AppSpecServiceArgs(
                        name="superagi",
                        image=do.AppSpecServiceImageArgs(
                            registry_name=registry.name,
                            repository="superagi",
                            tag=self.config.get("version", "latest"),
                        ),
                        instance_count=1,
                        instance_size_slug="professional-xs",
                        envs=env_vars,
                        health_check=do.AppSpecServiceHealthCheckArgs(
                            path="/health", port=3000, initial_delay_seconds=30
                        ),
                    )
                ],
            ),
        )

        # Export useful endpoints
        pulumi.export("superagi_url", self.app.live_url)
        pulumi.export("container_registry", registry.endpoint)


# Example usage
if __name__ == "__main__":
    config = Config()
    deployment = SuperAGIDeployment(
        name="ai-agent",
        config={
            "region": config.require("region"),
            "db_url": config.require("db_url"),
            "weaviate_url": config.require("weaviate_url"),
            "env": config.get("env", "production"),
        },
    )
