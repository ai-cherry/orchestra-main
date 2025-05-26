"""
Pulumi deployment for Orchestra AI on DigitalOcean
Uses existing Phidata/MCP framework instead of SuperAGI
"""

import pulumi
import pulumi_digitalocean as do
from pulumi import Config, Output

# Configuration
config = Config()
env = pulumi.get_stack()  # dev or prod

# Environment-specific settings
droplet_configs = {
    "dev": {
        "size": "s-1vcpu-2gb",  # $10/month
        "name": "orchestra-ai-dev",
        "tags": ["orchestra", "dev", "ai-agents"],
    },
    "prod": {
        "size": "s-2vcpu-8gb",  # $48/month
        "name": "orchestra-ai-prod",
        "tags": ["orchestra", "prod", "ai-agents"],
    },
}

droplet_config = droplet_configs.get(env, droplet_configs["dev"])

# Create SSH key
ssh_key = do.SshKey(
    "orchestra-ssh-key",
    name=f"orchestra-{env}-key",
    public_key=config.require("ssh_public_key"),
)

# Cloud-init script to set up the environment
cloud_init = """#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker

# Install Python 3.10
apt-get install -y python3.10 python3.10-venv python3-pip

# Create app directory
mkdir -p /opt/orchestra-ai
cd /opt/orchestra-ai

# Clone repository (or copy from CI/CD)
# git clone https://github.com/your-repo/orchestra-ai.git .

# Create .env file with connection strings
cat > .env << EOF
DRAGONFLY_URI=rediss://default:${DRAGONFLY_PASSWORD}@${DRAGONFLY_HOST}:6385
MONGO_URI=mongodb+srv://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_CLUSTER}
WEAVIATE_URL=${WEAVIATE_URL}
WEAVIATE_API_KEY=${WEAVIATE_API_KEY}
ENVIRONMENT=${ENVIRONMENT}
EOF

# Build and run with docker-compose
docker-compose up -d
"""

# Create Droplet
droplet = do.Droplet(
    "orchestra-droplet",
    name=droplet_config["name"],
    size=droplet_config["size"],
    image="ubuntu-22-04-x64",
    region="sfo3",
    ssh_keys=[ssh_key.id],
    tags=droplet_config["tags"],
    user_data=cloud_init.format(
        DRAGONFLY_PASSWORD=config.require_secret("dragonfly_password"),
        DRAGONFLY_HOST=config.require("dragonfly_host"),
        MONGO_USER=config.require("mongo_user"),
        MONGO_PASSWORD=config.require_secret("mongo_password"),
        MONGO_CLUSTER=config.require("mongo_cluster"),
        WEAVIATE_URL=config.require("weaviate_url"),
        WEAVIATE_API_KEY=config.require_secret("weaviate_api_key"),
        ENVIRONMENT=env,
    ),
    monitoring=True,
    backups=env == "prod",  # Only backup prod
)

# Create firewall rules
firewall = do.Firewall(
    "orchestra-firewall",
    name=f"orchestra-{env}-firewall",
    droplet_ids=[droplet.id],
    inbound_rules=[
        do.FirewallInboundRuleArgs(
            protocol="tcp",
            port_range="22",
            source_addresses=["0.0.0.0/0"],  # Restrict in production
        ),
        do.FirewallInboundRuleArgs(
            protocol="tcp", port_range="80", source_addresses=["0.0.0.0/0"]
        ),
        do.FirewallInboundRuleArgs(
            protocol="tcp", port_range="443", source_addresses=["0.0.0.0/0"]
        ),
        do.FirewallInboundRuleArgs(
            protocol="tcp",
            port_range="8080",  # Orchestra API
            source_addresses=["0.0.0.0/0"],
        ),
    ],
    outbound_rules=[
        do.FirewallOutboundRuleArgs(
            protocol="tcp", port_range="1-65535", destination_addresses=["0.0.0.0/0"]
        )
    ],
)

# Create a floating IP for production
if env == "prod":
    floating_ip = do.FloatingIp("orchestra-ip", region="sfo3", droplet_id=droplet.id)
    pulumi.export("floating_ip", floating_ip.ip_address)

# Outputs
pulumi.export("droplet_ip", droplet.ipv4_address)
pulumi.export("droplet_id", droplet.id)
pulumi.export("droplet_status", droplet.status)
pulumi.export("api_endpoint", Output.concat("http://", droplet.ipv4_address, ":8080"))
