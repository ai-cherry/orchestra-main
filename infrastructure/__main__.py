"""
Pulumi Infrastructure Configuration for AI Orchestrator
Provisions Vultr server, PostgreSQL, and integrations with Weaviate/Airbyte Cloud
"""

import pulumi
import pulumi_vultr as vultr
import pulumi_postgresql as postgresql
from pulumi import Config, Output, export
import json

# Get configuration
config = Config()
environment = config.get("environment") or "production"
vultr_region = config.get("vultr_region") or "ewr"  # New Jersey
instance_plan = config.get("instance_plan") or "vc2-4c-8gb"  # 4 vCPU, 8GB RAM

# Tags for resource organization
tags = {
    "Environment": environment,
    "Project": "ai-orchestrator",
    "ManagedBy": "pulumi"
}

# Create SSH key for server access
ssh_key = vultr.SshKey("ai-orchestrator-ssh-key",
    name=f"ai-orchestrator-{environment}",
    ssh_key=config.require_secret("ssh_public_key")
)

# Create firewall group
firewall_group = vultr.FirewallGroup("ai-orchestrator-fw",
    description=f"AI Orchestrator Firewall - {environment}"
)

# Firewall rules
firewall_rules = [
    # SSH access (restricted in production)
    vultr.FirewallRule("ssh-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0 if environment == "development" else 32,
        port="22",
        notes="SSH access"
    ),
    # HTTP/HTTPS for web services
    vultr.FirewallRule("http-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="80",
        notes="HTTP access"
    ),
    vultr.FirewallRule("https-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="443",
        notes="HTTPS access"
    ),
    # PostgreSQL (restricted to VPC in production)
    vultr.FirewallRule("postgres-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="10.0.0.0",
        subnet_size=8,
        port="5432",
        notes="PostgreSQL access"
    ),
    # MCP Server
    vultr.FirewallRule("mcp-server-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="8080",
        notes="MCP Server API"
    ),
]

# Create VPC for private networking
vpc = vultr.Vpc("ai-orchestrator-vpc",
    region=vultr_region,
    description=f"AI Orchestrator VPC - {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# User data script for server initialization
user_data = """#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-client \
    git \
    curl \
    wget \
    htop \
    vim \
    tmux \
    build-essential \
    libpq-dev

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker root

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/ai-orchestrator
cd /opt/ai-orchestrator

# Clone repository (placeholder - will be replaced by deployment)
# git clone https://github.com/your-org/ai-orchestrator.git .

# Set up Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Create systemd service for MCP server
cat > /etc/systemd/system/orchestrator-mcp.service << 'EOF'
[Unit]
Description=AI Orchestrator MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-orchestrator
Environment="PATH=/opt/ai-orchestrator/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/ai-orchestrator/venv/bin/python /opt/ai-orchestrator/mcp_server/orchestrator_mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for AI orchestrator
cat > /etc/systemd/system/ai-orchestrator.service << 'EOF'
[Unit]
Description=AI Orchestrator Service
After=network.target orchestrator-mcp.service
Requires=orchestrator-mcp.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-orchestrator
Environment="PATH=/opt/ai-orchestrator/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/ai-orchestrator/venv/bin/python /opt/ai-orchestrator/ai_components/orchestration/ai_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services (but don't start yet - waiting for deployment)
systemctl daemon-reload
systemctl enable orchestrator-mcp
systemctl enable ai-orchestrator

# Set up monitoring
apt-get install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Configure automatic updates
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Set up log rotation
cat > /etc/logrotate.d/ai-orchestrator << 'EOF'
/opt/ai-orchestrator/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

echo "Server initialization complete"
"""

# Create the main server instance
server = vultr.Instance("ai-orchestrator-server",
    region=vultr_region,
    plan=instance_plan,
    os_id=1743,  # Ubuntu 22.04 LTS
    label=f"ai-orchestrator-{environment}",
    hostname=f"ai-orchestrator-{environment}",
    enable_ipv6=True,
    backups="enabled" if environment == "production" else "disabled",
    ddos_protection=True if environment == "production" else False,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    user_data=user_data,
    tags=[f"{k}:{v}" for k, v in tags.items()]
)

# Create PostgreSQL database on Vultr Managed Database
postgres_db = vultr.Database("ai-orchestrator-db",
    database_engine="pg",
    database_engine_version="15",
    region=vultr_region,
    plan="vultr-dbaas-startup-cc-1-25-2",  # 1 vCPU, 1GB RAM, 25GB storage
    label=f"ai-orchestrator-db-{environment}",
    tag=f"Environment:{environment}",
    cluster_time_zone="America/New_York",
    maintenance_dow="sunday",
    maintenance_time="03:00",
    
    # PostgreSQL specific settings
    mysql_sql_modes=None,
    mysql_require_primary_key=None,
    redis_eviction_policy=None,
    
    # Network configuration
    trusted_ips=["10.0.0.0/24"],  # VPC subnet
    
    # High availability for production
    read_replicas=1 if environment == "production" else 0,
)

# Create database and user
postgres_provider = postgresql.Provider("postgres-provider",
    host=postgres_db.host,
    port=postgres_db.port,
    database="postgres",
    username=postgres_db.user,
    password=postgres_db.password,
    sslmode="require",
    connect_timeout=15,
)

# Create application database
app_database = postgresql.Database("orchestrator-db",
    name="orchestrator",
    owner=postgres_db.user,
    lc_collate="en_US.UTF-8",
    lc_ctype="en_US.UTF-8",
    opts=postgresql.DatabaseOptsArgs(
        provider=postgres_provider
    )
)

# Create application user
app_user = postgresql.Role("orchestrator-user",
    name="orchestrator_app",
    password=config.require_secret("postgres_app_password"),
    login=True,
    opts=postgresql.RoleOptsArgs(
        provider=postgres_provider
    )
)

# Grant privileges
app_user_grant = postgresql.Grant("orchestrator-user-grant",
    database=app_database.name,
    role=app_user.name,
    object_type="database",
    privileges=["CREATE", "CONNECT", "TEMPORARY"],
    opts=postgresql.GrantOptsArgs(
        provider=postgres_provider,
        depends_on=[app_database, app_user]
    )
)

# Create schema
app_schema = postgresql.Schema("orchestrator-schema",
    name="orchestrator",
    database=app_database.name,
    owner=app_user.name,
    opts=postgresql.SchemaOptsArgs(
        provider=postgres_provider,
        depends_on=[app_database, app_user]
    )
)

# Create monitoring stack (Prometheus + Grafana)
monitoring_compose = """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
"""

# Prometheus configuration
prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
  
  - job_name: 'mcp-server'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
"""

# Output important values
export("server_ip", server.main_ip)
export("server_ipv6", server.v6_main_ip)
export("vpc_subnet", vpc.v4_subnet)
export("postgres_host", postgres_db.host)
export("postgres_port", postgres_db.port)
export("postgres_database", app_database.name)
export("postgres_user", app_user.name)
export("postgres_endpoint", Output.concat(
    "postgresql://", app_user.name, ":", 
    config.require_secret("postgres_app_password"),
    "@", postgres_db.host, ":", postgres_db.port.apply(str), 
    "/", app_database.name, "?sslmode=require"
))
export("mcp_server_url", Output.concat("http://", server.main_ip, ":8080"))

# Stack outputs for reference
export("stack_outputs", {
    "environment": environment,
    "region": vultr_region,
    "server": {
        "id": server.id,
        "ip": server.main_ip,
        "ipv6": server.v6_main_ip,
        "plan": instance_plan,
        "os": "Ubuntu 22.04 LTS"
    },
    "database": {
        "id": postgres_db.id,
        "engine": "PostgreSQL 15",
        "plan": postgres_db.plan,
        "replicas": postgres_db.read_replicas
    },
    "networking": {
        "vpc_id": vpc.id,
        "vpc_subnet": vpc.v4_subnet,
        "firewall_group_id": firewall_group.id
    },
    "services": {
        "mcp_server": "http://server:8080",
        "prometheus": "http://server:9090",
        "grafana": "http://server:3000"
    },
    "integrations": {
        "weaviate": "Configured via environment",
        "airbyte": "Configured via environment"
    }
})