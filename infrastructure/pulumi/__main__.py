"""
Pulumi infrastructure for AI Orchestra on Vultr
"""
import pulumi
import pulumi_vultr as vultr
import pulumi_command as command
from pulumi import Config, Output, export

# Get configuration
config = Config()
region = config.get("region") or "ewr"  # New Jersey by default
instance_type = config.get("instanceType") or "vc2-2c-4gb"  # 2 vCPU, 4GB RAM
ssh_key_name = config.get("sshKeyName") or "orchestra-key"

# Create SSH key if not exists
ssh_key = vultr.SshKey("orchestra-ssh-key",
    name=ssh_key_name,
    ssh_key=config.require_secret("sshPublicKey")
)

# Create a firewall group
firewall_group = vultr.FirewallGroup("orchestra-firewall",
    description="Firewall rules for AI Orchestra"
)

# Add firewall rules
ssh_rule = vultr.FirewallRule("ssh-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="22"
)

http_rule = vultr.FirewallRule("http-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="80"
)

https_rule = vultr.FirewallRule("https-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="443"
)

api_rule = vultr.FirewallRule("api-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="8000"
)

# Create the Vultr instance
instance = vultr.Instance("orchestra-instance",
    region=region,
    plan=instance_type,
    os_id=387,  # Ubuntu 22.04 LTS
    label="AI Orchestra API",
    hostname="orchestra-api",
    enable_ipv6=True,
    backups="disabled",
    ddos_protection=False,
    activation_email=False,
    ssh_key_ids=[ssh_key.id],
    firewall_group_id=firewall_group.id,
    user_data="""#!/bin/bash
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

# Install nginx
apt-get install -y nginx

# Create directories
mkdir -p /opt/orchestra/config
mkdir -p /opt/orchestra/data

# Configure nginx
cat > /etc/nginx/sites-available/orchestra <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
systemctl restart nginx
"""
)

# Copy and deploy the Docker image
deploy_script = command.remote.Command("deploy-orchestra",
    connection=command.remote.ConnectionArgs(
        host=instance.main_ip,
        user="root",
        private_key=config.require_secret("sshPrivateKey"),
    ),
    create=Output.concat("""
# Wait for instance to be ready
sleep 30

# Copy Docker image
echo "Copying Docker image..."
"""),
    opts=pulumi.ResourceOptions(depends_on=[instance])
)

# Export outputs
export("instance_id", instance.id)
export("instance_ip", instance.main_ip)
export("instance_ipv6", instance.v6_main_ip)
export("api_url", Output.concat("http://", instance.main_ip))
export("ssh_command", Output.concat("ssh root@", instance.main_ip))