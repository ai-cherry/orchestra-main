"""
DigitalOcean infrastructure core stack.
Modular, type-safe Pulumi implementation for AI workloads.
"""

from typing import Dict
import pulumi
from pulumi import Config, Output
import pulumi_digitalocean as do


class CoreStack:
    def __init__(self, name: str, config: Dict[str, str]):
        """
        Initialize core infrastructure components.

        Args:
            name: Stack name prefix for resources
            config: Dictionary of configuration values
        """
        self._name = name
        self.config = config
        self._setup_networking()
        self._setup_databases()
        self._setup_compute()

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
                do.FirewallInboundRuleArgs(
                    protocol="tcp", port_range="22", source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp", port_range="80", source_addresses=["0.0.0.0/0"]
                ),
            ],
        )

    def _setup_databases(self) -> None:
        """Provision database services."""
        # DragonflyDB for caching
        self.dragonfly = do.DatabaseCluster(
            f"{self._name}-dragonfly",
            engine="dragonfly",
            version="1.8",
            node_count=3,
            region=self.config["region"],
            size="db-s-2vcpu-4gb",
        )

        # Weaviate for vector search
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

    def _setup_compute(self) -> None:
        """Configure compute resources for SuperAGI."""
        self.superagi = do.Droplet(
            f"{self._name}-superagi",
            image="docker-20-04",
            region=self.config["region"],
            size="s-4vcpu-8gb",
            user_data="""#!/bin/bash
            docker run -d \
                -p 3000:3000 \
                -e DB_URL=redis://${DB_HOST} \
                -e WEAVIATE_URL=${WEAVIATE_URL} \
                transformeroptimus/superagi
            """,
        )

        # Export useful outputs
        pulumi.export("dragonfly_uri", self.dragonfly.uri)
        pulumi.export(
            "weaviate_url", Output.concat("https://", self.weaviate.default_ingress)
        )
        pulumi.export("superagi_ip", self.superagi.ipv4_address)


# Example usage
if __name__ == "__main__":
    config = Config()
    stack = CoreStack(
        name="ai-core",
        config={"region": config.require("region"), "env": config.require("env")},
    )
