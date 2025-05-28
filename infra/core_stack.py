"""
DigitalOcean infrastructure core stack with ESC integration.
Modular, type-safe Pulumi implementation for AI workloads.
"""

from typing import Dict

import pulumi
import pulumi_digitalocean as do
from pulumi import Config, Output


class CoreStack:
    def __init__(self, name: str, config: Dict[str, str]):
        """
        Initialize core infrastructure components with ESC support.

        Args:
            name: Stack name prefix for resources
            config: Dictionary of configuration values
        """
        self._name = name
        self.config = config
        self._setup_esc_environment()
        self._setup_networking()
        self._setup_databases()
        self._setup_compute()

    def _setup_esc_environment(self) -> None:
        """Create ESC environment configuration with Paperspace support."""
        env = self.config.get("env", "dev")
        provider = self.config.get("provider", "digitalocean")

        if provider == "paperspace":
            self.esc_env_name = "orchestra-ai/dev-paperspace"
            self.is_paperspace = True
            # Standardized environment prefix
            self.env_prefix = "PAPERSPACE"
        else:
            self.esc_env_name = f"orchestra-ai/{env}-app-config"
            self.is_paperspace = False

        # Export ESC environment name for application use
        pulumi.export("esc_environment", self.esc_env_name)
        pulumi.export("is_paperspace", self.is_paperspace)

    def _setup_networking(self) -> None:
        """Configure VPC and firewall rules."""
        self.vpc = do.Vpc(
            f"{self._name}-vpc",
            region=self.config.get("region", "nyc3"),
            ip_range="10.0.0.0/16",
        )

        self.firewall = do.Firewall(
            f"{self._name}-fw",
            droplet_ids=[],
            inbound_rules=[
                do.FirewallInboundRuleArgs(protocol="tcp", port_range="22", source_addresses=["0.0.0.0/0"]),
                do.FirewallInboundRuleArgs(protocol="tcp", port_range="80", source_addresses=["0.0.0.0/0"]),
            ],
        )

    def _setup_databases(self) -> None:
        """Provision database services with Paperspace support."""
        if not self.is_paperspace:
            # DigitalOcean managed services
            self.dragonfly = do.DatabaseCluster(
                f"{self._name}-dragonfly",
                engine="dragonfly",
                version="1.8",
                node_count=3,
                region=self.config["region"],
                size="db-s-2vcpu-4gb",
            )

            self.mongodb = do.DatabaseCluster(
                f"{self._name}-mongodb",
                engine="mongodb",
                version="6.0",
                node_count=3,
                region=self.config["region"],
                size="db-s-2vcpu-4gb",
            )

            self.weaviate = do.App(
                f"{self._name}-weaviate",
                spec=do.AppSpecArgs(
                    name="weaviate",
                    region=self.config["region"],
                    services=[
                        {
                            "name": "weaviate",
                            "image": "semitechnologies/weaviate:1.30",
                            "instance_size_slug": "professional-xs",
                            "envs": [
                                {"key": "AUTHENTICATION_APIKEY_ENABLED", "value": "true"},
                                {
                                    "key": "PERSISTENCE_DATA_PATH",
                                    "value": "/var/lib/weaviate",
                                },
                            ],
                        }
                    ],
                ),
            )

            # Export DO service endpoints
            pulumi.export("mongo_uri", self.mongodb.uri)
            pulumi.export("dragonfly_uri", self.dragonfly.uri)
            pulumi.export("weaviate_url", Output.concat("https://", self.weaviate.default_ingress))
        else:
            # Paperspace local services
            pulumi.export("mongo_uri", "mongodb://localhost:27017")
            pulumi.export("dragonfly_uri", "redis://localhost:6379")
            pulumi.export("weaviate_url", "http://localhost:8080")

    def _setup_compute(self) -> None:
        """Configure compute resources with ESC integration."""
        _ = self.config.get("env", "dev")  # Used for ESC env name construction

        if not self.is_paperspace:
            # DigitalOcean droplet configuration
            startup_script = f"""#!/bin/bash
            # Load ESC environment variables
            eval $(pulumi env open {self.esc_env_name} --shell=sh)

            # Start application
            docker run -d \\
                -p 3000:3000 \\
                -e DB_URL=$MONGO_URI \\
                -e WEAVIATE_URL=$WEAVIATE_URL \\
                transformeroptimus/superagi
            """

            self.superagi = do.Droplet(
                f"{self._name}-superagi",
                image="docker-20-04",
                region=self.config["region"],
                size="s-4vcpu-8gb",
                user_data=startup_script,
            )

            # Export useful outputs
            pulumi.export("superagi_ip", self.superagi.ipv4_address)
        else:
            # Paperspace local configuration
            startup_script = f"""#!/bin/bash
            # Load ESC environment variables
            eval $(pulumi env open {self.esc_env_name} --shell=sh)

            # Start application with Paperspace-specific ports
            docker run -d \\
                -p 8000:8000 \\
                -e DB_URL=${self.env_prefix}_MONGO_URI \\
                -e WEAVIATE_URL=${self.env_prefix}_WEAVIATE_URL \\
                transformeroptimus/superagi
            """

            pulumi.export("startup_script", startup_script)


# Example usage
if __name__ == "__main__":
    config = Config()
    stack = CoreStack(
        name="ai-core",
        config={"region": config.require("region"), "env": config.require("env")},
    )
