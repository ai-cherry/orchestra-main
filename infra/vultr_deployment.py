# TODO: Consider adding connection pooling configuration
"""
"""
project_name = "cherry-ai"
environment = config.get("environment") or "production"

# Create tags for resource management
tags = {
    "project": project_name,
    "environment": environment,
    "managed-by": "pulumi"
}

# Create a VPC for network isolation
vpc = vultr.Vpc(f"{project_name}-vpc",
    region="ewr",  # New Jersey region
    description=f"VPC for {project_name} {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create firewall group
firewall_group = vultr.FirewallGroup(f"{project_name}-firewall",
    description=f"Firewall for {project_name} {environment}"
)

# Add firewall rules
# Allow SSH from anywhere (restrict this in production)
ssh_rule = vultr.FirewallRule(f"{project_name}-ssh-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
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

# Allow backend API port
api_rule = vultr.FirewallRule(f"{project_name}-api-rule",
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="8000"
)

# Create the main server instance
server = vultr.Instance(f"{project_name}-server",
    region="ewr",
    plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
    os_id=1743,  # Ubuntu 22.04 LTS
    label=f"{project_name}-{environment}",
    hostname=f"{project_name}-{environment}",
    enable_ipv6=True,
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    tags=[f"project:{project_name}", f"env:{environment}"]
)

# Create a reserved IP for the server
reserved_ip = vultr.ReservedIp(f"{project_name}-ip",
    region="ewr",
    ip_type="v4",
    label=f"{project_name}-{environment}-ip"
)

# Attach the reserved IP to the server
ip_attachment = vultr.InstanceIpv4(f"{project_name}-ip-attach",
    instance_id=server.id,
    ip=reserved_ip.subnet
)

# Create object storage for backups and static files
object_storage = vultr.ObjectStorage(f"{project_name}-storage",
    cluster_id=2,  # New Jersey cluster
    label=f"{project_name}-{environment}-storage"
)

# Create a database instance (optional, for future use)
database = vultr.Database(f"{project_name}-db",
    database_engine="pg",
    database_engine_version="15",
    region="ewr",
    plan="vultr-dbaas-hobbyist-cc-1-25-1",
    label=f"{project_name}-{environment}-db",
    tag=f"project:{project_name}",
    cluster_time_zone="America/New_York",
    trusted_ips=["0.0.0.0/0"]  # Restrict this in production
)

# Export important values
export("server_id", server.id)
export("server_ip", server.main_ip)
export("reserved_ip", reserved_ip.subnet)
export("vpc_id", vpc.id)
export("firewall_group_id", firewall_group.id)
export("object_storage_id", object_storage.id)
export("object_storage_hostname", object_storage.s3_hostname)
export("database_id", database.id)
export("database_host", database.host)
export("database_port", database.port)
export("database_name", database.dbname)
export("database_user", database.user)

# Create a startup script for the server
startup_script = vultr.StartupScript(f"{project_name}-startup",
    name=f"{project_name}-{environment}-startup",
    script="""
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install nginx
apt-get install -y nginx certbot python3-certbot-nginx

# Create app directory
mkdir -p /opt/orchestra

# Configure nginx (basic setup, will be updated later)
cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
    }
}
EOF

# Restart nginx
systemctl restart nginx

# Enable firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "Server setup complete!"
"""
    type="boot"
)

# Output the startup script ID for reference
export("startup_script_id", startup_script.id)