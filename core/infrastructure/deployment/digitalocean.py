"""
DigitalOcean implementation of the CloudProvider interface.

This module provides DigitalOcean-specific deployment operations.
"""

from typing import Any, Dict, List, Optional

import pulumi_digitalocean as do
from pulumi import Output

from .base import CloudProvider, DeploymentConfig, ResourceSize

class DigitalOceanProvider(CloudProvider):
    """DigitalOcean implementation of CloudProvider."""

    # Map our generic sizes to DigitalOcean droplet sizes
    SIZE_MAPPING = {
        ResourceSize.SMALL: "s-1vcpu-2gb",  # $10/month
        ResourceSize.MEDIUM: "s-2vcpu-4gb",  # $24/month
        ResourceSize.LARGE: "s-4vcpu-8gb",  # $48/month
        ResourceSize.XLARGE: "s-8vcpu-16gb",  # $96/month
    }

    def __init__(self, config: DeploymentConfig, ssh_key_id: Optional[str] = None):
        super().__init__(config)
        self.ssh_key_id = ssh_key_id
        self._created_resources = []

    def create_compute_instance(self, name: str, image: str, user_data: Optional[str] = None) -> Output[str]:
        """Create a DigitalOcean droplet and return its IP address."""
        # Map generic image names to DigitalOcean slugs
        image_mapping = {
            "ubuntu-22-04-x64": "ubuntu-22-04-x64",
            "ubuntu-20-04-x64": "ubuntu-20-04-x64",
            "debian-11-x64": "debian-11-x64",
        }

        do_image = image_mapping.get(image, image)
        do_size = self.SIZE_MAPPING[self.config.resource_size]

        # Create the droplet
        droplet = do.Droplet(
            name,
            name=name,
            size=do_size,
            image=do_image,
            region=self.config.region,
            ssh_keys=[self.ssh_key_id] if self.ssh_key_id else [],
            tags=list(self.config.tags.values()),
            user_data=user_data,
            monitoring=self.config.enable_monitoring,
            backups=self.config.enable_backups,
        )

        self._created_resources.append(droplet)
        return droplet.ipv4_address

    def create_managed_database(self, name: str, engine: str, version: str) -> Output[Dict[str, Any]]:
        """Create a managed database cluster."""
        # Map generic engine names to DigitalOcean engines
        engine_mapping = {
            "postgresql": "pg",
            "mysql": "mysql",
            "redis": "redis",
            "mongodb": "mongodb",
        }

        do_engine = engine_mapping.get(engine, engine)

        # Determine node size based on environment
        if self.config.environment.value == "prod":
            node_size = "db-s-2vcpu-4gb"
            node_count = 2
        else:
            node_size = "db-s-1vcpu-2gb"
            node_count = 1

        # Create the database cluster
        db_cluster = do.DatabaseCluster(
            name,
            name=name,
            engine=do_engine,
            version=version,
            size=node_size,
            region=self.config.region,
            node_count=node_count,
            tags=list(self.config.tags.values()),
        )

        self._created_resources.append(db_cluster)

        # Return connection information
        return Output.all(
            host=db_cluster.host,
            port=db_cluster.port,
            user=db_cluster.user,
            password=db_cluster.password,
            database=db_cluster.database,
            uri=db_cluster.uri,
        ).apply(
            lambda args: {
                "host": args["host"],
                "port": args["port"],
                "user": args["user"],
                "password": args["password"],
                "database": args["database"],
                "uri": args["uri"],
            }
        )

    def create_object_storage(self, name: str, public: bool = False) -> Output[str]:
        """Create a Spaces bucket (DigitalOcean's S3-compatible storage)."""
        # Create the Space
        space = do.SpacesBucket(
            name,
            name=name,
            region=self.config.region,
            acl="public-read" if public else "private",
        )

        self._created_resources.append(space)

        # Return the bucket endpoint
        return space.bucket_domain_name

    def create_firewall_rules(self, name: str, rules: List[Dict[str, Any]]) -> Any:
        """Create firewall rules for DigitalOcean droplets."""
        # Convert generic rules to DigitalOcean format
        inbound_rules = []

        for rule in rules:
            inbound_rule = do.FirewallInboundRuleArgs(
                protocol=rule["protocol"],
                port_range=str(rule["port"]),
                source_addresses=[rule.get("source", "0.0.0.0/0")],
            )
            inbound_rules.append(inbound_rule)

        # Default outbound rule (allow all)
        outbound_rules = [
            do.FirewallOutboundRuleArgs(
                protocol="tcp",
                port_range="1-65535",
                destination_addresses=["0.0.0.0/0"],
            ),
            do.FirewallOutboundRuleArgs(
                protocol="udp",
                port_range="1-65535",
                destination_addresses=["0.0.0.0/0"],
            ),
        ]

        # Get droplet IDs from created resources
        droplet_ids = [r.id for r in self._created_resources if isinstance(r, do.Droplet)]

        # Create the firewall
        firewall = do.Firewall(
            name,
            name=name,
            droplet_ids=droplet_ids,
            inbound_rules=inbound_rules,
            outbound_rules=outbound_rules,
            tags=list(self.config.tags.values()),
        )

        return firewall
