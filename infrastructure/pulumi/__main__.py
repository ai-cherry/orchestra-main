"""
Cherry AI Orchestrator - Infrastructure as Code
Pulumi configuration for automated infrastructure management
"""

import pulumi
import pulumi_lambda as Lambda
import pulumi_random as random
from pulumi import Config, Output

# Configuration
config = Config()
LAMBDA_API_KEY = config.require_secret("LAMBDA_API_KEY")

# Create SSH key for server access
ssh_key = lambda.SshKey("cherry-ai-ssh-key",
    name="cherry-ai-orchestrator",
    ssh_key=config.require("ssh_public_key")
)

# Production server
production_server = lambda.Instance("cherry-ai-production",
    plan="vc2-16c-64gb",  # 16 vCPUs, 64GB RAM
    region="lax",  # Los Angeles
    os_id=1743,  # Ubuntu 24.04 LTS
    label="cherry-ai-production",
    tag="production",
    hostname="cherry-ai-production",
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    user_data="""#!/bin/bash
# Initial server setup
apt update && apt upgrade -y
apt install -y nginx redis-server python3-pip nodejs npm curl git htop

# Configure firewall
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Start services
systemctl start nginx redis-server
systemctl enable nginx redis-server

# Create application user
useradd -m -s /bin/bash cherry-ai
usermod -aG sudo cherry-ai

# Setup application directory
mkdir -p /var/www/cherry-ai
chown -R cherry-ai:cherry-ai /var/www/cherry-ai

echo "✅ Server initialization completed"
"""
)

# Database server
database_server = lambda.Instance("cherry-ai-database",
    plan="vc2-8c-32gb",  # 8 vCPUs, 32GB RAM
    region="lax",  # Los Angeles
    os_id=1743,  # Ubuntu 24.04 LTS
    label="cherry-ai-database",
    tag="database",
    hostname="cherry-ai-database",
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    user_data="""#!/bin/bash
# Database server setup
apt update && apt upgrade -y
apt install -y postgresql postgresql-contrib redis-server

# Configure PostgreSQL
sudo -u postgres createuser orchestra
sudo -u postgres createdb cherry_ai
sudo -u postgres psql -c "ALTER USER orchestra PASSWORD 'orchestra_prod_2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cherry_ai TO orchestra;"

# Configure Redis
systemctl start postgresql redis-server
systemctl enable postgresql redis-server

echo "✅ Database server setup completed"
"""
)

# Staging server
staging_server = lambda.Instance("cherry-ai-staging",
    plan="vc2-4c-8gb",  # 4 vCPUs, 8GB RAM
    region="lax",  # Los Angeles
    os_id=1743,  # Ubuntu 24.04 LTS
    label="cherry-ai-staging",
    tag="staging",
    hostname="cherry-ai-staging",
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    user_data="""#!/bin/bash
# Staging server setup
apt update && apt upgrade -y
apt install -y nginx redis-server python3-pip nodejs npm curl git

systemctl start nginx redis-server
systemctl enable nginx redis-server

echo "✅ Staging server setup completed"
"""
)

# Load balancer
load_balancer = lambda.LoadBalancer("cherry-ai-lb",
    region="lax",
    label="cherry-ai-load-balancer",
    balancing_algorithm="roundrobin",
    proxy_protocol=False,
    health_check={
        "protocol": "http",
        "port": 80,
        "path": "/health",
        "check_interval": 15,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 2
    },
    forwarding_rules=[
        {
            "frontend_protocol": "http",
            "frontend_port": 80,
            "backend_protocol": "http",
            "backend_port": 80
        },
        {
            "frontend_protocol": "https",
            "frontend_port": 443,
            "backend_protocol": "http",
            "backend_port": 80
        }
    ],
    instances=[production_server.id]
)

# Kubernetes cluster for scaling
k8s_cluster = lambda.KubernetesCluster("cherry-ai-k8s",
    region="lax",
    version="v1.28.0+1",
    label="cherry-ai-k8s",
    node_pools=[
        {
            "node_quantity": 3,
            "plan": "vc2-2c-4gb",
            "label": "worker-nodes",
            "tag": "worker"
        }
    ]
)

# DNS records (if using Lambda DNS)
# domain = lambda.DnsDomain("cherry-ai-me",
#     domain="cherry-ai.me"
# )

# a_record = lambda.DnsRecord("cherry-ai-a-record",
#     domain=domain.domain,
#     name="",
#     type="A",
#     data=production_server.main_ip,
#     ttl=300
# )

# www_record = lambda.DnsRecord("cherry-ai-www-record",
#     domain=domain.domain,
#     name="www",
#     type="A",
#     data=production_server.main_ip,
#     ttl=300
# )

# Outputs
pulumi.export("production_server_ip", production_server.main_ip)
pulumi.export("production_server_id", production_server.id)
pulumi.export("database_server_ip", database_server.main_ip)
pulumi.export("database_server_id", database_server.id)
pulumi.export("staging_server_ip", staging_server.main_ip)
pulumi.export("staging_server_id", staging_server.id)
pulumi.export("load_balancer_ip", load_balancer.ipv4)
pulumi.export("k8s_cluster_endpoint", k8s_cluster.endpoint)
pulumi.export("ssh_key_id", ssh_key.id)

