#!/usr/bin/env python3
"""
Vultr Infrastructure Deployment using Pulumi
Deploys cherry_ai MCP infrastructure on Vultr
"""

import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output, export
import os
import json

# Configuration
config = Config()
project_name = "conductor-mcp"
environment = config.get("environment") or "production"

# Vultr regions
region = config.get("region") or "ewr"  # New Jersey

# Instance sizes (Vultr plan IDs)
instance_plans = {
    "small": "vc2-1c-2gb",      # 1 vCPU, 2GB RAM
    "medium": "vc2-2c-4gb",      # 2 vCPU, 4GB RAM  
    "large": "vc2-4c-8gb",       # 4 vCPU, 8GB RAM
    "xlarge": "vc2-8c-16gb"      # 8 vCPU, 16GB RAM
}

# Create VPC
vpc = vultr.Vpc(f"{project_name}-vpc",
    region=region,
    description=f"{project_name} VPC",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create Firewall Group
firewall_group = vultr.FirewallGroup(f"{project_name}-firewall",
    description=f"{project_name} Firewall Rules"
)

# Firewall Rules
firewall_rules = [
    # SSH
    {"protocol": "tcp", "port": "22", "source": "0.0.0.0/0", "notes": "SSH"},
    # HTTP/HTTPS
    {"protocol": "tcp", "port": "80", "source": "0.0.0.0/0", "notes": "HTTP"},
    {"protocol": "tcp", "port": "443", "source": "0.0.0.0/0", "notes": "HTTPS"},
    # API
    {"protocol": "tcp", "port": "8000", "source": "0.0.0.0/0", "notes": "API"},
    # PostgreSQL (internal only)
    {"protocol": "tcp", "port": "5432", "source": "10.0.0.0/24", "notes": "PostgreSQL"},
    # Redis (internal only)
    {"protocol": "tcp", "port": "6379", "source": "10.0.0.0/24", "notes": "Redis"},
    # Weaviate
    {"protocol": "tcp", "port": "8080", "source": "10.0.0.0/24", "notes": "Weaviate"},
    # Monitoring
    {"protocol": "tcp", "port": "9090", "source": "10.0.0.0/24", "notes": "Prometheus"},
    {"protocol": "tcp", "port": "3000", "source": "0.0.0.0/0", "notes": "Grafana"},
]

for i, rule in enumerate(firewall_rules):
    vultr.FirewallRule(f"{project_name}-fw-rule-{i}",
        firewall_group_id=firewall_group.id,
        protocol=rule["protocol"],
        port=rule["port"],
        source=rule["source"],
        notes=rule["notes"]
    )

# SSH Key
ssh_key = vultr.SshKey(f"{project_name}-ssh-key",
    name=f"{project_name}-key",
    ssh_key=config.require("ssh_public_key")
)

# User data script for instance initialization
user_data = """#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install monitoring tools
apt-get install -y htop iotop nethogs

# Setup swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Configure sysctl for performance
cat >> /etc/sysctl.conf <<EOF
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
EOF
sysctl -p

# Create app directory
mkdir -p /opt/cherry_ai
chown -R ubuntu:ubuntu /opt/cherry_ai
"""

# Database Server
db_server = vultr.Instance(f"{project_name}-db",
    region=region,
    plan=instance_plans["large"],  # 4 vCPU, 8GB for DB
    os_id=1743,  # Ubuntu 22.04 LTS
    label=f"{project_name}-db-{environment}",
    hostname=f"{project_name}-db",
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    user_data=user_data,
    tags=[project_name, environment, "database"]
)

# Application Servers (multiple for HA)
app_servers = []
app_count = config.get_int("app_server_count") or 2

for i in range(app_count):
    app_server = vultr.Instance(f"{project_name}-app-{i}",
        region=region,
        plan=instance_plans["medium"],  # 2 vCPU, 4GB for apps
        os_id=1743,  # Ubuntu 22.04 LTS
        label=f"{project_name}-app-{i}-{environment}",
        hostname=f"{project_name}-app-{i}",
        enable_ipv6=True,
        backups="enabled",
        ddos_protection=True,
        activation_email=False,
        ssh_key_ids=[ssh_key.id],
        firewall_group_id=firewall_group.id,
        vpc_ids=[vpc.id],
        user_data=user_data,
        tags=[project_name, environment, "application"]
    )
    app_servers.append(app_server)

# Load Balancer
load_balancer = vultr.LoadBalancer(f"{project_name}-lb",
    region=region,
    label=f"{project_name}-lb-{environment}",
    balancing_algorithm="roundrobin",
    proxy_protocol=False,
    ssl_redirect=True,
    http2=True,
    
    forwarding_rules=[
        {
            "frontend_protocol": "https",
            "frontend_port": 443,
            "backend_protocol": "http",
            "backend_port": 8000
        },
        {
            "frontend_protocol": "http",
            "frontend_port": 80,
            "backend_protocol": "http", 
            "backend_port": 8000
        }
    ],
    
    health_check={
        "protocol": "http",
        "port": 8000,
        "path": "/health",
        "check_interval": 10,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 2
    },
    
    instances=[server.id for server in app_servers],
    
    ssl={
        "private_key": config.get("ssl_private_key"),
        "certificate": config.get("ssl_certificate"),
        "chain": config.get("ssl_chain")
    } if config.get("ssl_certificate") else None
)

# Object Storage for backups
object_storage = vultr.ObjectStorage(f"{project_name}-storage",
    cluster_id=1,  # New Jersey cluster
    label=f"{project_name}-backups-{environment}"
)

# Reserved IPs for static addressing
reserved_ip = vultr.ReservedIp(f"{project_name}-ip",
    region=region,
    ip_type="v4",
    label=f"{project_name}-static-ip"
)

# Attach reserved IP to load balancer
vultr.ReservedIpAttachment(f"{project_name}-ip-attach",
    reserved_ip_id=reserved_ip.id,
    instance_id=load_balancer.id
)

# Outputs
export("vpc_id", vpc.id)
export("load_balancer_ip", load_balancer.ipv4)
export("load_balancer_ipv6", load_balancer.ipv6)
export("db_server_ip", db_server.main_ip)
export("db_server_private_ip", db_server.internal_ip)
export("app_server_ips", [server.main_ip for server in app_servers])
export("app_server_private_ips", [server.internal_ip for server in app_servers])
export("object_storage_endpoint", object_storage.s3_hostname)
export("reserved_ip", reserved_ip.subnet)

# Create deployment info file
deployment_info = {
    "environment": environment,
    "region": region,
    "vpc_id": vpc.id,
    "load_balancer": {
        "ip": load_balancer.ipv4,
        "ipv6": load_balancer.ipv6
    },
    "database": {
        "public_ip": db_server.main_ip,
        "private_ip": db_server.internal_ip,
        "plan": instance_plans["large"]
    },
    "app_servers": [
        {
            "public_ip": server.main_ip,
            "private_ip": server.internal_ip,
            "plan": instance_plans["medium"]
        } for server in app_servers
    ],
    "storage": {
        "endpoint": object_storage.s3_hostname,
        "region": object_storage.region
    }
}

# Save deployment info
Output.all(deployment_info).apply(
    lambda info: open(f"deployment-{environment}.json", "w").write(json.dumps(info, indent=2))
)