# TODO: Consider adding connection pooling configuration
"""
"""
project_name = config.get("project_name") or "orchestra-memory"
environment = config.get("environment") or "production"
region = config.get("region") or "ewr"  # New Jersey
ssh_key_id = config.require("ssh_key_id")  # Vultr SSH key ID

# Resource naming
def resource_name(name: str) -> str:
    """Generate consistent resource names."""
    return f"{project_name}-{environment}-{name}"

# VPC Network
vpc = vultr.Vpc(
    resource_name("vpc"),
    region=region,
    description=f"VPC for {project_name} {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=16,
)

# Firewall Rules
firewall_group = vultr.FirewallGroup(
    resource_name("firewall"),
    description=f"Firewall for {project_name} {environment}",
)

# Allow internal VPC traffic
vultr.FirewallRule(
    resource_name("fw-internal"),
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="10.0.0.0",
    subnet_size=16,
    port="1-65535",
    source="10.0.0.0/16",
    notes="Allow internal VPC traffic",
)

# Allow SSH from specific IPs (update with your IP)
vultr.FirewallRule(
    resource_name("fw-ssh"),
    firewall_group_id=firewall_group.id,
    protocol="tcp",
    ip_type="v4",
    subnet="0.0.0.0",
    subnet_size=0,
    port="22",
    notes="Allow SSH access",
)

# Allow HTTP/HTTPS
for port, name in [(80, "http"), (443, "https")]:
    vultr.FirewallRule(
        resource_name(f"fw-{name}"),
        firewall_group_id=firewall_group.id,
        protocol="tcp",
        ip_type="v4",
        subnet="0.0.0.0",
        subnet_size=0,
        port=str(port),
        notes=f"Allow {name.upper()} traffic",
    )

# PostgreSQL Database Instance (High Performance)
postgres_instance = vultr.Instance(
    resource_name("postgres"),
    plan="vc2-4c-8gb",  # 4 vCPU, 8GB RAM
    region=region,
    os_id=387,  # Ubuntu 22.04 LTS
    label=f"{project_name} PostgreSQL",
    hostname=resource_name("postgres"),
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key_id],
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    user_data=base64.b64encode("""
"""
    resource_name("redis"),
    plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
    region=region,
    os_id=387,  # Ubuntu 22.04 LTS
    label=f"{project_name} Redis",
    hostname=resource_name("redis"),
    enable_ipv6=True,
    backups="enabled",
    ddos_protection=True,
    activation_email=False,
    ssh_key_ids=[ssh_key_id],
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    user_data=base64.b64encode("""
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Advanced Config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

# Set up Redis systemd service
systemctl restart redis-server
systemctl enable redis-server

# Install Redis exporter for Prometheus
wget https://github.com/oliver006/redis_exporter/releases/download/v1.45.0/redis_exporter-v1.45.0.linux-amd64.tar.gz
tar xvfz redis_exporter-v1.45.0.linux-amd64.tar.gz
mv redis_exporter-v1.45.0.linux-amd64/redis_exporter /usr/local/bin/
rm -rf redis_exporter-v1.45.0.linux-amd64*

# Create systemd service for Redis exporter
cat > /etc/systemd/system/redis_exporter.service << EOF
[Unit]
Description=Redis Exporter
After=network.target

[Service]
Type=simple
User=redis
Environment="REDIS_PASSWORD=CHANGE_ME_SECURE_PASSWORD"
ExecStart=/usr/local/bin/redis_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable redis_exporter
systemctl start redis_exporter
"""
        resource_name(f"app-{i+1}"),
        plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
        region=region,
        os_id=387,  # Ubuntu 22.04 LTS
        label=f"{project_name} App Server {i+1}",
        hostname=resource_name(f"app-{i+1}"),
        enable_ipv6=True,
        backups="enabled",
        ddos_protection=True,
        activation_email=False,
        ssh_key_ids=[ssh_key_id],
        firewall_group_id=firewall_group.id,
        vpc_ids=[vpc.id],
        user_data=base64.b64encode(f"""
environment=PATH="/home/orchestra/venv/bin"
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/orchestra << EOF
server {{
    listen 80;
    server_name _;
    
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\$host;
        proxy_cache_bypass \\$http_upgrade;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
    }}
    
    location /metrics {{
        proxy_pass http://127.0.0.1:9090;
    }}
}}
EOF

ln -s /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Create log directory
mkdir -p /var/log/orchestra
chown orchestra:orchestra /var/log/orchestra

# Start services
systemctl restart nginx
systemctl restart supervisor

# Install Node Exporter for monitoring
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
mv node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-1.5.0.linux-amd64*

cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter
"""
    resource_name("lb"),
    region=region,
    label=f"{project_name} Load Balancer",
    vpc_id=vpc.id,
    forwarding_rules=[
        {
            "frontend_protocol": "http",
            "frontend_port": 80,
            "backend_protocol": "http",
            "backend_port": 80,
        },
        {
            "frontend_protocol": "https",
            "frontend_port": 443,
            "backend_protocol": "http",
            "backend_port": 80,
        }
    ],
    health_check={
        "protocol": "http",
        "port": 80,
        "path": "/health",
        "check_interval": 10,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 3,
    },
    ssl_redirect=True,
    proxy_protocol=False,
    balancing_algorithm="roundrobin",
    instances=[instance.id for instance in app_instances],
)

# Monitoring Server (Prometheus + Grafana)
monitoring_instance = vultr.Instance(
    resource_name("monitoring"),
    plan="vc2-1c-2gb",  # 1 vCPU, 2GB RAM
    region=region,
    os_id=387,  # Ubuntu 22.04 LTS
    label=f"{project_name} Monitoring",
    hostname=resource_name("monitoring"),
    enable_ipv6=True,
    backups="enabled",
    activation_email=False,
    ssh_key_ids=[ssh_key_id],
    firewall_group_id=firewall_group.id,
    vpc_ids=[vpc.id],
    user_data=base64.b64encode(f"""
      - targets: [{', '.join([f"'{instance.internal_ip}:9100'" for instance in app_instances])}]
  
  - job_name: 'app'
    static_configs:
      - targets: [{', '.join([f"'{instance.internal_ip}:9090'" for instance in app_instances])}]
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['{postgres_instance.internal_ip}:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['{redis_instance.internal_ip}:9121']
EOF

# Configure Grafana
cat > /etc/grafana/grafana.ini << EOF
[server]
http_port = 3000
domain = monitoring.{project_name}.com

[security]
admin_user = admin
admin_password = CHANGE_ME_SECURE_PASSWORD

[auth.anonymous]
enabled = false

[alerting]
enabled = true

[unified_alerting]
enabled = true
EOF

# Start services
systemctl restart prometheus
systemctl enable prometheus
systemctl restart grafana-server
systemctl enable grafana-server

# Configure Nginx for Grafana
apt-get install -y nginx
cat > /etc/nginx/sites-available/grafana << EOF
server {{
    listen 80;
    server_name _;
    
    location / {{
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
    }}
}}
EOF

ln -s /etc/nginx/sites-available/grafana /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
systemctl restart nginx
"""
pulumi.export("vpc_id", vpc.id)
pulumi.export("postgres_ip", postgres_instance.main_ip)
pulumi.export("redis_ip", redis_instance.main_ip)
pulumi.export("load_balancer_ip", load_balancer.ipv4)
pulumi.export("monitoring_ip", monitoring_instance.main_ip)
pulumi.export("app_server_ips", [instance.main_ip for instance in app_instances])

# Connection strings
pulumi.export("postgres_connection", Output.concat(
    "postgresql://orchestra_user:CHANGE_ME_SECURE_PASSWORD@",
    postgres_instance.internal_ip,
    ":5432/orchestra_memory"
))
pulumi.export("redis_connection", Output.concat(
    "redis://:CHANGE_ME_SECURE_PASSWORD@",
    redis_instance.internal_ip,
    ":6379"
))
pulumi.export("monitoring_url", Output.concat(
    "http://",
    monitoring_instance.main_ip,
    ":3000"
))
pulumi.export("app_url", Output.concat(
    "http://",
    load_balancer.ipv4
))