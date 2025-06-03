#!/usr/bin/env python3
"""
Pulumi deployment script for Vultr infrastructure with comprehensive orchestrator
"""

import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output, export
import json
import base64

# Get configuration
config = Config()
project_name = "orchestra-ai"

# Get secrets from environment
vultr_api_key = config.require_secret("vultr_api_key")
db_password = config.require_secret("db_password")
jwt_secret = config.require_secret("jwt_secret")

# Region configuration
region = config.get("region") or "ewr"  # New Jersey

# Create VPC
vpc = vultr.Vpc(f"{project_name}-vpc",
    region=region,
    description="Orchestra AI VPC",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create firewall group
firewall_group = vultr.FirewallGroup(f"{project_name}-firewall",
    description="Orchestra AI Firewall Rules"
)

# Firewall rules
firewall_rules = [
    # SSH
    vultr.FirewallRule(f"{project_name}-ssh-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="22"
    ),
    # HTTP
    vultr.FirewallRule(f"{project_name}-http-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="80"
    ),
    # HTTPS
    vultr.FirewallRule(f"{project_name}-https-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="443"
    ),
    # PostgreSQL (internal only)
    vultr.FirewallRule(f"{project_name}-postgres-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="10.0.0.0",
        subnet_size=24,
        port="5432"
    ),
    # Weaviate
    vultr.FirewallRule(f"{project_name}-weaviate-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="8080"
    ),
    # MCP WebSocket
    vultr.FirewallRule(f"{project_name}-mcp-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="8765"
    ),
    # Cursor Integration
    vultr.FirewallRule(f"{project_name}-cursor-rule",
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port="8090"
    )
]

# User data script for instance initialization
def create_user_data(role: str, db_host: str) -> str:
    script = f"""#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y docker.io docker-compose git python3-pip postgresql-client nginx

# Clone repository
git clone https://github.com/orchestra/main.git /opt/orchestra
cd /opt/orchestra

# Create environment file
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://orchestra:{db_password}@{db_host}:5432/orchestra

# Orchestrator Configuration
ORCHESTRATOR_ROLE={role}
WORKSPACE_PATH=/opt/orchestra
ENABLE_AUTOSCALING=true

# API Keys (will be populated from secrets)
JWT_SECRET={jwt_secret}
VULTR_API_KEY={vultr_api_key}
EOF

# Add all API keys from config
echo "$(cat /opt/api_keys.env)" >> .env

# Install Python dependencies
pip3 install -r requirements.txt

# Start services based on role
if [ "{role}" == "master" ]; then
    # Start comprehensive orchestrator
    python3 ai_components/orchestration/comprehensive_orchestrator.py &
    
    # Configure nginx as load balancer
    cp /opt/orchestra/nginx.conf /etc/nginx/sites-available/default
    systemctl restart nginx
    
elif [ "{role}" == "worker" ]; then
    # Start worker agent
    python3 ai_components/orchestration/worker_agent.py &
    
elif [ "{role}" == "database" ]; then
    # Install and configure PostgreSQL
    apt-get install -y postgresql postgresql-contrib
    
    # Configure PostgreSQL
    sudo -u postgres psql << SQL
CREATE USER orchestra WITH PASSWORD '{db_password}';
CREATE DATABASE orchestra OWNER orchestra;
GRANT ALL PRIVILEGES ON DATABASE orchestra TO orchestra;
SQL
    
    # Allow remote connections
    echo "host all all 10.0.0.0/24 md5" >> /etc/postgresql/*/main/pg_hba.conf
    echo "listen_addresses = '*'" >> /etc/postgresql/*/main/postgresql.conf
    systemctl restart postgresql
    
elif [ "{role}" == "weaviate" ]; then
    # Run Weaviate
    docker run -d \\
        --name weaviate \\
        --restart always \\
        -p 8080:8080 \\
        -e QUERY_DEFAULTS_LIMIT=25 \\
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \\
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \\
        -e DEFAULT_VECTORIZER_MODULE=text2vec-openai \\
        semitechnologies/weaviate:latest
fi

# Enable service on boot
cat > /etc/systemd/system/orchestra.service << 'EOF'
[Unit]
Description=Orchestra AI Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/orchestra
ExecStart=/usr/bin/python3 /opt/orchestra/ai_components/orchestration/comprehensive_orchestrator.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable orchestra
systemctl start orchestra
"""
    return base64.b64encode(script.encode()).decode()

# Create database instance
db_instance = vultr.Instance(f"{project_name}-db",
    plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM for database
    region=region,
    os_id=387,  # Ubuntu 20.04
    label=f"{project_name}-database",
    hostname=f"{project_name}-db",
    enable_ipv6=True,
    vpc_ids=[vpc.id],
    firewall_group_id=firewall_group.id,
    user_data=create_user_data("database", "localhost"),
    backups="enabled",
    ddos_protection=True
)

# Create Weaviate instance
weaviate_instance = vultr.Instance(f"{project_name}-weaviate",
    plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
    region=region,
    os_id=387,  # Ubuntu 20.04
    label=f"{project_name}-weaviate",
    hostname=f"{project_name}-weaviate",
    enable_ipv6=True,
    vpc_ids=[vpc.id],
    firewall_group_id=firewall_group.id,
    user_data=create_user_data("weaviate", db_instance.internal_ip),
    backups="enabled"
)

# Create master orchestrator instance
master_instance = vultr.Instance(f"{project_name}-master",
    plan="vc2-4c-8gb",  # 4 vCPU, 8GB RAM for master
    region=region,
    os_id=387,  # Ubuntu 20.04
    label=f"{project_name}-master",
    hostname=f"{project_name}-master",
    enable_ipv6=True,
    vpc_ids=[vpc.id],
    firewall_group_id=firewall_group.id,
    user_data=create_user_data("master", db_instance.internal_ip),
    backups="enabled",
    ddos_protection=True
)

# Create initial worker instances
worker_instances = []
for i in range(2):  # Start with 2 workers
    worker = vultr.Instance(f"{project_name}-worker-{i}",
        plan="vc2-1c-2gb",  # 1 vCPU, 2GB RAM for workers
        region=region,
        os_id=387,  # Ubuntu 20.04
        label=f"{project_name}-worker-{i}",
        hostname=f"{project_name}-worker-{i}",
        enable_ipv6=True,
        vpc_ids=[vpc.id],
        firewall_group_id=firewall_group.id,
        user_data=create_user_data("worker", db_instance.internal_ip),
        backups="enabled"
    )
    worker_instances.append(worker)

# Create load balancer
load_balancer = vultr.LoadBalancer(f"{project_name}-lb",
    region=region,
    label=f"{project_name}-load-balancer",
    vpc_id=vpc.id,
    forwarding_rules=[{
        "frontend_protocol": "http",
        "frontend_port": 80,
        "backend_protocol": "http",
        "backend_port": 8080
    }, {
        "frontend_protocol": "tcp",
        "frontend_port": 8765,
        "backend_protocol": "tcp",
        "backend_port": 8765
    }],
    health_check={
        "protocol": "http",
        "port": 8080,
        "path": "/health",
        "check_interval": 10,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 2
    },
    instances=[master_instance.id] + [w.id for w in worker_instances]
)

# Create DNS records
dns_domain = vultr.DnsDomain(f"{project_name}-domain",
    domain="orchestra-ai.com",
    ip=load_balancer.ipv4
)

dns_records = [
    vultr.DnsRecord(f"{project_name}-www",
        domain=dns_domain.domain,
        name="www",
        type="A",
        data=load_balancer.ipv4
    ),
    vultr.DnsRecord(f"{project_name}-api",
        domain=dns_domain.domain,
        name="api",
        type="A",
        data=load_balancer.ipv4
    ),
    vultr.DnsRecord(f"{project_name}-mcp",
        domain=dns_domain.domain,
        name="mcp",
        type="A",
        data=master_instance.main_ip
    )
]

# Export outputs
export("load_balancer_ip", load_balancer.ipv4)
export("master_ip", master_instance.main_ip)
export("database_ip", db_instance.internal_ip)
export("weaviate_ip", weaviate_instance.internal_ip)
export("api_endpoint", Output.concat("http://", load_balancer.ipv4))
export("mcp_websocket", Output.concat("ws://", master_instance.main_ip, ":8765"))
export("cursor_api", Output.concat("http://", master_instance.main_ip, ":8090"))
export("worker_count", len(worker_instances))