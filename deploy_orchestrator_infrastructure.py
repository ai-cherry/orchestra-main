#!/usr/bin/env python3
"""
Cherry AI Orchestrator Infrastructure Deployment
Using Pulumi for Vultr infrastructure provisioning
"""

import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output, export
import json
import base64

# Configuration
config = Config()
project_name = "cherry-ai-orchestrator"
environment = config.get("environment") or "production"
region = config.get("region") or "ewr"  # New Jersey

# Tags for resource management
tags = {
    "project": project_name,
    "environment": environment,
    "managed-by": "pulumi",
    "component": "orchestrator"
}

# Create VPC for network isolation
vpc = vultr.Vpc(f"{project_name}-vpc",
    region=region,
    description=f"VPC for {project_name} {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create firewall group
firewall_group = vultr.FirewallGroup(f"{project_name}-fw",
    description=f"Firewall for {project_name} {environment}"
)

# Firewall rules
# Allow SSH from specific IPs (update with your IP)
ssh_rule = vultr.FirewallRule(f"{project_name}-ssh-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,  # Update to restrict SSH access
    port="22"
)

# Allow HTTP
http_rule = vultr.FirewallRule(f"{project_name}-http-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="80"
)

# Allow HTTPS
https_rule = vultr.FirewallRule(f"{project_name}-https-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="443"
)

# Allow API port
api_rule = vultr.FirewallRule(f"{project_name}-api-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="8000"
)

# Create startup script for instance initialization
startup_script_content = """#!/bin/bash
set -euo pipefail

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    rsync \
    htop \
    ufw \
    fail2ban

# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Configure fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Create web directory
mkdir -p /var/www/cherry-ai-orchestrator

# Configure nginx
cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/cherry-ai-orchestrator;
    index cherry-ai-orchestrator-final.html index.html;
    
    server_name _;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Restart nginx
systemctl restart nginx

# Create deployment user
useradd -m -s /bin/bash deploy || true
usermod -aG www-data deploy

# Set up monitoring
apt-get install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

echo "Instance initialization complete"
"""

startup_script = vultr.StartupScript(f"{project_name}-startup",
    name=f"{project_name}-init-{environment}",
    script=base64.b64encode(startup_script_content.encode()).decode()
)

# Get the latest Ubuntu 22.04 LTS OS
os_list = vultr.get_os_list()
ubuntu_os = next((os for os in os_list.oss if "Ubuntu 22.04" in os.name), None)

# Instance configuration based on environment
instance_plans = {
    "production": "vc2-2c-4gb",    # 2 vCPU, 4GB RAM
    "staging": "vc2-1c-2gb",        # 1 vCPU, 2GB RAM
    "development": "vc2-1c-1gb"     # 1 vCPU, 1GB RAM
}

plan = instance_plans.get(environment, "vc2-1c-2gb")

# Create main instance
instance = vultr.Instance(f"{project_name}-instance",
    region=region,
    plan=plan,
    os_id=ubuntu_os.id if ubuntu_os else 387,  # Ubuntu 22.04 LTS
    label=f"{project_name}-{environment}",
    hostname=f"{project_name}-{environment}",
    enable_ipv6=True,
    backups="enabled" if environment == "production" else "disabled",
    ddos_protection=True if environment == "production" else False,
    activation_email=False,
    vpc_ids=[vpc.id],
    firewall_group_id=firewall_group.id,
    script_id=startup_script.id,
    tags=[f"{k}:{v}" for k, v in tags.items()]
)

# Create object storage for backups and static assets
object_storage = vultr.ObjectStorage(f"{project_name}-storage",
    cluster_id=1,  # New Jersey cluster
    label=f"{project_name}-{environment}-storage"
)

# Create DNS records if domain is configured
domain_name = config.get("domain")
if domain_name:
    # Create DNS domain if it doesn't exist
    domain = vultr.DnsDomain(f"{project_name}-domain",
        domain=domain_name,
        ip=instance.main_ip
    )
    
    # A record for root domain
    a_record = vultr.DnsRecord(f"{project_name}-a-record",
        domain=domain_name,
        name="orchestrator",
        type="A",
        data=instance.main_ip,
        ttl=300
    )
    
    # AAAA record for IPv6
    aaaa_record = vultr.DnsRecord(f"{project_name}-aaaa-record",
        domain=domain_name,
        name="orchestrator",
        type="AAAA",
        data=instance.v6_main_ip,
        ttl=300
    )
    
    # CNAME for www
    www_record = vultr.DnsRecord(f"{project_name}-www-record",
        domain=domain_name,
        name="www.orchestrator",
        type="CNAME",
        data=f"orchestrator.{domain_name}",
        ttl=300
    )

# Create snapshot schedule for production
if environment == "production":
    snapshot_schedule = vultr.SnapshotSchedule(f"{project_name}-snapshots",
        instance_id=instance.id,
        schedule_type="daily",
        hour=3,  # 3 AM UTC
        dow=0,   # Not used for daily
        dom=0    # Not used for daily
    )

# Reserved IP for production environment
if environment == "production":
    reserved_ip = vultr.ReservedIp(f"{project_name}-ip",
        region=region,
        ip_type="v4",
        label=f"{project_name}-{environment}-ip"
    )
    
    # Attach reserved IP to instance
    ip_attachment = vultr.InstanceIpv4(f"{project_name}-ip-attach",
        instance_id=instance.id,
        reboot=False
    )

# Monitoring and alerting setup
monitoring_config = {
    "metrics_retention": "30d" if environment == "production" else "7d",
    "alert_endpoints": {
        "email": config.get("alert_email"),
        "webhook": config.get("alert_webhook")
    },
    "thresholds": {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "bandwidth_mbps": 100
    }
}

# Export outputs
export("instance_id", instance.id)
export("instance_ip", instance.main_ip)
export("instance_ipv6", instance.v6_main_ip)
export("vpc_id", vpc.id)
export("firewall_group_id", firewall_group.id)
export("object_storage_id", object_storage.id)
export("object_storage_endpoint", object_storage.s3_hostname)

if domain_name:
    export("domain", domain_name)
    export("orchestrator_url", f"https://orchestrator.{domain_name}")

# Create deployment info file
deployment_info = {
    "project": project_name,
    "environment": environment,
    "region": region,
    "instance": {
        "id": instance.id,
        "ip": instance.main_ip,
        "ipv6": instance.v6_main_ip,
        "plan": plan
    },
    "networking": {
        "vpc_id": vpc.id,
        "firewall_group_id": firewall_group.id
    },
    "storage": {
        "object_storage_id": object_storage.id,
        "endpoint": object_storage.s3_hostname
    },
    "monitoring": monitoring_config
}

# Output deployment configuration
pulumi.export("deployment_config", deployment_info)

# Create post-deployment script
post_deploy_script = f"""#!/bin/bash
# Post-deployment configuration for Cherry AI Orchestrator

echo "Waiting for instance to be ready..."
sleep 30

# SSH into instance and complete setup
ssh -o StrictHostKeyChecking=no root@{instance.main_ip} << 'ENDSSH'
# Deploy application files
cd /var/www/cherry-ai-orchestrator
curl -O https://raw.githubusercontent.com/your-repo/cherry-ai-orchestrator-final.html
curl -O https://raw.githubusercontent.com/your-repo/cherry-ai-orchestrator.js

# Set permissions
chown -R www-data:www-data /var/www/cherry-ai-orchestrator
chmod -R 755 /var/www/cherry-ai-orchestrator

# Configure SSL with Let's Encrypt
certbot --nginx -d orchestrator.{domain_name} -d www.orchestrator.{domain_name} --non-interactive --agree-tos -m {config.get('email')}

# Restart services
systemctl restart nginx

echo "Deployment complete!"
ENDSSH
"""

# Save post-deployment script
with open("post_deploy_orchestrator.sh", "w") as f:
    f.write(post_deploy_script)

print(f"""
Cherry AI Orchestrator Infrastructure Deployed!
==============================================
Environment: {environment}
Instance IP: {instance.main_ip}
VPC ID: {vpc.id}

Next steps:
1. Run: chmod +x post_deploy_orchestrator.sh
2. Run: ./post_deploy_orchestrator.sh
3. Access your orchestrator at: https://orchestrator.{domain_name}

To destroy infrastructure:
pulumi destroy

To update infrastructure:
pulumi up
""")