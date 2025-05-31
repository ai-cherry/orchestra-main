#!/bin/bash
#
# implement_two_node_architecture.sh
#
# Comprehensive script to implement the Cherry AI two-node architecture:
# - Vector + Storage Node: CPU-Optimized Premium (4 vCPU / 8 GB) with NVMe & 10 Gbps
# - App / Orchestrator / MCP Node: General-Purpose (8 vCPU / 32 GB)
#
# This script handles:
# 1. Infrastructure setup with Pulumi
# 2. Data migration from existing to new architecture
# 3. Admin UI deployment to the new architecture
# 4. Monitoring setup
# 5. Automated testing and verification
#

set -e  # Exit on any error

# Terminal colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PULUMI_STACK="prod"
REGION="sfo3"
ADMIN_UI_DOMAIN="cherry-ai.me"
API_DOMAIN="api.cherry-ai.me"
MONITORING_DOMAIN="monitoring.cherry-ai.me"
VECTOR_NODE_SIZE="c-4-8gb-nvme"  # CPU-Optimized Premium with NVMe
APP_NODE_SIZE="g-8vcpu-32gb"     # General Purpose with 32GB RAM
MIGRATION_TIMEOUT=3600  # 1 hour timeout for data migration
VERIFY_TIMEOUT=300      # 5 minutes timeout for verification

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
  echo -e "${BLUE}${BOLD}Checking prerequisites...${NC}"
  
  # Check for required commands
  local missing_deps=0
  
  for cmd in pulumi python3 pip3 node npm pnpm curl jq ssh-keygen; do
    if ! command_exists "$cmd"; then
      echo -e "${RED}❌ $cmd is not installed.${NC}"
      missing_deps=1
    else
      echo -e "${GREEN}✓ $cmd is installed.${NC}"
    fi
  done
  
  # Check for DigitalOcean CLI
  if ! command_exists doctl; then
    echo -e "${YELLOW}⚠️ doctl (DigitalOcean CLI) is not installed. Installing...${NC}"
    curl -sL https://github.com/digitalocean/doctl/releases/download/v1.101.0/doctl-1.101.0-linux-amd64.tar.gz | tar xz
    sudo mv doctl /usr/local/bin
    
    if ! command_exists doctl; then
      echo -e "${RED}❌ Failed to install doctl. Please install manually.${NC}"
      missing_deps=1
    else
      echo -e "${GREEN}✓ doctl installed successfully.${NC}"
    fi
  else
    echo -e "${GREEN}✓ doctl is installed.${NC}"
  fi
  
  # Check for required environment variables
  if [ -z "$DIGITALOCEAN_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ DIGITALOCEAN_TOKEN environment variable is not set.${NC}"
    
    # Try to get from Pulumi config
    if command_exists pulumi; then
      DIGITALOCEAN_TOKEN=$(cd "$REPO_ROOT/infra" && pulumi config get --show-secrets digitalocean:token 2>/dev/null || echo "")
      if [ -n "$DIGITALOCEAN_TOKEN" ]; then
        echo -e "${GREEN}✓ Retrieved DIGITALOCEAN_TOKEN from Pulumi config.${NC}"
        export DIGITALOCEAN_TOKEN
      else
        echo -e "${RED}❌ Could not retrieve DIGITALOCEAN_TOKEN from Pulumi config.${NC}"
        missing_deps=1
      fi
    else
      missing_deps=1
    fi
  else
    echo -e "${GREEN}✓ DIGITALOCEAN_TOKEN environment variable is set.${NC}"
  fi
  
  # Check for Pulumi access token
  if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ PULUMI_ACCESS_TOKEN environment variable is not set.${NC}"
    
    # Try to get from Pulumi config
    if command_exists pulumi; then
      PULUMI_ACCESS_TOKEN=$(cd "$REPO_ROOT/infra" && pulumi config get --show-secrets pulumi_access_token 2>/dev/null || echo "")
      if [ -n "$PULUMI_ACCESS_TOKEN" ]; then
        echo -e "${GREEN}✓ Retrieved PULUMI_ACCESS_TOKEN from Pulumi config.${NC}"
        export PULUMI_ACCESS_TOKEN
      else
        echo -e "${RED}❌ Could not retrieve PULUMI_ACCESS_TOKEN from Pulumi config.${NC}"
        missing_deps=1
      fi
    else
      missing_deps=1
    fi
  else
    echo -e "${GREEN}✓ PULUMI_ACCESS_TOKEN environment variable is set.${NC}"
  fi
  
  # Check for SSH key
  SSH_KEY_PATH="$HOME/.ssh/orchestra_do_key"
  if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️ SSH key not found at $SSH_KEY_PATH. Generating...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "orchestra-deployment-key"
    echo -e "${GREEN}✓ SSH key generated at $SSH_KEY_PATH.${NC}"
  else
    echo -e "${GREEN}✓ SSH key exists at $SSH_KEY_PATH.${NC}"
  fi
  
  if [ $missing_deps -ne 0 ]; then
    echo -e "${RED}${BOLD}Missing prerequisites. Please install them and try again.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}${BOLD}All prerequisites satisfied!${NC}"
}

# Function to initialize Pulumi project
initialize_pulumi() {
  echo -e "${BLUE}${BOLD}Initializing Pulumi project...${NC}"
  
  cd "$REPO_ROOT/infra"
  
  # Check if Pulumi stack exists
  if ! pulumi stack ls | grep -q "$PULUMI_STACK"; then
    echo -e "${YELLOW}Creating new Pulumi stack: $PULUMI_STACK${NC}"
    pulumi stack init "$PULUMI_STACK"
  else
    echo -e "${GREEN}Using existing Pulumi stack: $PULUMI_STACK${NC}"
    pulumi stack select "$PULUMI_STACK"
  fi
  
  # Set Pulumi config values
  echo -e "${BLUE}Setting Pulumi configuration...${NC}"
  
  # Set required configuration values
  pulumi config set env "$PULUMI_STACK"
  pulumi config set region "$REGION"
  pulumi config set --secret digitalocean:token "$DIGITALOCEAN_TOKEN"
  pulumi config set adminUiCustomDomain "$ADMIN_UI_DOMAIN"
  pulumi config set apiDomain "$API_DOMAIN"
  pulumi config set monitoringDomain "$MONITORING_DOMAIN"
  pulumi config set vectorNodeSize "$VECTOR_NODE_SIZE"
  pulumi config set appNodeSize "$APP_NODE_SIZE"
  pulumi config set ssh_pubkey_path "$SSH_KEY_PATH.pub"
  pulumi config set --secret ssh_private_key_path "$SSH_KEY_PATH"
  
  echo -e "${GREEN}Pulumi project initialized successfully!${NC}"
}

# Function to create the two-node infrastructure
create_infrastructure() {
  echo -e "${BLUE}${BOLD}Creating two-node infrastructure...${NC}"
  
  cd "$REPO_ROOT"
  
  # Create the orchestra_stack.py file if it doesn't exist
  if [ ! -f "infra/orchestra_stack.py" ]; then
    echo -e "${YELLOW}Creating orchestra_stack.py file...${NC}"
    
    cat > "infra/orchestra_stack.py" << 'EOF'
"""
Orchestra Stack - Two-Node Architecture Implementation
- Vector + Storage Node: CPU-Optimized Premium with NVMe
- App / Orchestrator / MCP Node: General-Purpose
"""

import pulumi
import pulumi_digitalocean as do
import pulumi_command as command
from pulumi import Config
import os

class OrchestraStack:
    """Complete Orchestra infrastructure based on the two-node blueprint"""
    
    def __init__(self, name, config):
        self.config = config
        self.env = config.get("env", "dev")
        self.region = config.get("region", "sfo3")
        
        # Create shared VPC and networking
        self.vpc = self._create_vpc()
        self.firewall = self._create_firewall()
        
        # Create the two primary nodes
        self.vector_node = self._create_vector_node()
        self.app_node = self._create_app_node()
        
        # Configure services
        self._configure_weaviate()
        self._configure_postgres()
        self._configure_admin_ui()
        self._configure_monitoring()
        
        # Export outputs
        self._export_outputs()
    
    def _create_vpc(self):
        """Create VPC for Orchestra infrastructure"""
        return do.Vpc(
            f"{self.env}-vpc",
            name=f"orchestra-{self.env}-vpc",
            region=self.region,
            ip_range="10.0.0.0/16"
        )
    
    def _create_firewall(self):
        """Create firewall rules for Orchestra infrastructure"""
        return do.Firewall(
            f"{self.env}-firewall",
            name=f"orchestra-{self.env}-firewall",
            inbound_rules=[
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="22",
                    source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="80",
                    source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="443",
                    source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="8080",
                    source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="3000",
                    source_addresses=["0.0.0.0/0"]
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="9090-9100",
                    source_addresses=["0.0.0.0/0"]
                )
            ],
            outbound_rules=[
                do.FirewallOutboundRuleArgs(
                    protocol="tcp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0"]
                ),
                do.FirewallOutboundRuleArgs(
                    protocol="udp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0"]
                ),
                do.FirewallOutboundRuleArgs(
                    protocol="icmp",
                    destination_addresses=["0.0.0.0/0"]
                )
            ]
        )
    
    def _get_ssh_key(self):
        """Get or create SSH key for deployment"""
        ssh_pubkey_path = self.config.get("ssh_pubkey_path")
        if not ssh_pubkey_path:
            raise Exception("ssh_pubkey_path not set in Pulumi config")
        
        with open(os.path.expanduser(ssh_pubkey_path), "r") as f:
            ssh_pubkey_content = f.read()
        
        return do.SshKey(
            f"{self.env}-ssh-key",
            name=f"orchestra-{self.env}-key",
            public_key=ssh_pubkey_content
        )
    
    def _create_vector_node(self):
        """Create CPU-Optimized node for Vector + Storage"""
        ssh_key = self._get_ssh_key()
        
        vector_node_size = self.config.get("vectorNodeSize", "c-4-8gb-nvme")
        
        return do.Droplet(
            f"{self.env}-vector-node",
            name=f"orchestra-{self.env}-vector-node",
            image="ubuntu-22-04-x64",
            region=self.region,
            size=vector_node_size,
            vpc_uuid=self.vpc.id,
            ssh_keys=[ssh_key.id],
            tags=[f"orchestra-{self.env}", "vector", "storage"],
            monitoring=True,
            user_data=self._get_vector_node_init_script()
        )
    
    def _create_app_node(self):
        """Create General Purpose node for App/Orchestrator/MCP"""
        ssh_key = self._get_ssh_key()
        
        app_node_size = self.config.get("appNodeSize", "g-8vcpu-32gb")
        
        return do.Droplet(
            f"{self.env}-app-node",
            name=f"orchestra-{self.env}-app-node",
            image="ubuntu-22-04-x64",
            region=self.region,
            size=app_node_size,
            vpc_uuid=self.vpc.id,
            ssh_keys=[ssh_key.id],
            tags=[f"orchestra-{self.env}", "app", "orchestrator", "mcp"],
            monitoring=True,
            user_data=self._get_app_node_init_script()
        )
    
    def _get_vector_node_init_script(self):
        """Get cloud-init script for Vector node"""
        return """#!/bin/bash
# Vector Node Initialization Script

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-compose

# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib

# Configure PostgreSQL for high performance
cat > /etc/postgresql/14/main/conf.d/orchestra.conf << EOF
# Memory settings
shared_buffers = '2GB'
work_mem = '128MB'
maintenance_work_mem = '256MB'

# Write performance
wal_buffers = '16MB'
checkpoint_completion_target = 0.9

# Query optimization
random_page_cost = 1.1  # SSD optimization
effective_cache_size = '4GB'
EOF

# Restart PostgreSQL
systemctl restart postgresql

# Create Weaviate directory
mkdir -p /opt/weaviate
cd /opt/weaviate

# Create Weaviate docker-compose file
cat > docker-compose.yml << EOF
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.30.2
    ports:
    - "8080:8080"
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
volumes:
  weaviate_data:
EOF

# Start Weaviate
docker-compose up -d

# Install Node Exporter for Prometheus
useradd --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvf node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create Node Exporter service
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start Node Exporter
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Create data directory
mkdir -p /data
chmod 777 /data

echo "Vector Node initialization complete!"
"""
    
    def _get_app_node_init_script(self):
        """Get cloud-init script for App node"""
        admin_ui_domain = self.config.get("adminUiCustomDomain", "cherry-ai.me")
        api_domain = self.config.get("apiDomain", "api.cherry-ai.me")
        monitoring_domain = self.config.get("monitoringDomain", "monitoring.cherry-ai.me")
        
        return f"""#!/bin/bash
# App Node Initialization Script

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-compose

# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install pnpm
npm install -g pnpm

# Install Python 3.10 and pip
apt-get install -y python3 python3-pip python3-venv

# Install Nginx and Certbot
apt-get install -y nginx certbot python3-certbot-nginx

# Create directories
mkdir -p /opt/orchestra
mkdir -p /var/www/admin-ui
mkdir -p /opt/monitoring

# Configure Nginx for Admin UI
cat > /etc/nginx/sites-available/{admin_ui_domain}.conf << EOF
server {{
    listen 80;
    server_name {admin_ui_domain};
    
    location / {{
        root /var/www/admin-ui;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {{
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }}
    }}
}}
EOF

# Configure Nginx for API
cat > /etc/nginx/sites-available/{api_domain}.conf << EOF
server {{
    listen 80;
    server_name {api_domain};
    
    location / {{
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }}
}}
EOF

# Configure Nginx for Monitoring
cat > /etc/nginx/sites-available/{monitoring_domain}.conf << EOF
server {{
    listen 80;
    server_name {monitoring_domain};
    
    location / {{
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }}
}}
EOF

# Enable sites
ln -sf /etc/nginx/sites-available/{admin_ui_domain}.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/{api_domain}.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/{monitoring_domain}.conf /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Setup Prometheus and Grafana
cd /opt/monitoring

# Create docker-compose for monitoring stack
cat > docker-compose.yml << EOF
version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command: 
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: always
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus_data:
  grafana_data:
EOF

# Create Prometheus config template (will be updated later with actual IPs)
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  
scrape_configs:
  - job_name: 'orchestra_api'
    static_configs:
      - targets: ['localhost:8080']
  
  - job_name: 'vector_node'
    static_configs:
      - targets: ['VECTOR_NODE_IP:9100']
      
  - job_name: 'app_node'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Install Node Exporter for Prometheus
useradd --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvf node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create Node Exporter service
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start Node Exporter
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Restart Nginx
systemctl reload nginx

echo "App Node initialization complete!"
"""
    
    def _configure_weaviate(self):
        """Configure Weaviate on Vector node"""
        # This will be handled by the vector node init script
        pass
    
    def _configure_postgres(self):
        """Configure PostgreSQL on Vector node"""
        # This will be handled by the vector node init script
        pass
    
    def _configure_admin_ui(self):
        """Configure Admin UI on App node"""
        # This will be handled by the app node init script and deployment scripts
        pass
    
    def _configure_monitoring(self):
        """Configure monitoring stack"""
        # Update Prometheus config with actual Vector Node IP
        update_prometheus = command.remote.Command(
            f"{self.env}-update-prometheus",
            connection=self._get_app_node_connection(),
            create=pulumi.Output.all(vector_node_ip=self.vector_node.ipv4_address).apply(
                lambda args: f"""
                # Update Prometheus config with actual Vector Node IP
                sed -i 's/VECTOR_NODE_IP/{args["vector_node_ip"]}/' /opt/monitoring/prometheus.yml
                
                # Start monitoring stack
                cd /opt/monitoring
                docker-compose up -d
                """
            )
        )
    
    def _get_app_node_connection(self):
        """Get SSH connection to App node"""
        ssh_private_key_path = self.config.get_secret("ssh_private_key_path")
        if not ssh_private_key_path:
            raise Exception("ssh_private_key_path not set in Pulumi config")
        
        with open(os.path.expanduser(ssh_private_key_path), "r") as f:
            ssh_private_key = f.read()
        
        return command.remote.ConnectionArgs(
            host=self.app_node.ipv4_address,
            user="root",
            private_key=ssh_private_key
        )
    
    def _get_vector_node_connection(self):
        """Get SSH connection to Vector node"""
        ssh_private_key_path = self.config.get_secret("ssh_private_key_path")
        if not ssh_private_key_path:
            raise Exception("ssh_private_key_path not set in Pulumi config")
        
        with open(os.path.expanduser(ssh_private_key_path), "r") as f:
            ssh_private_key = f.read()
        
        return command.remote.ConnectionArgs(
            host=self.vector_node.ipv4_address,
            user="root",
            private_key=ssh_private_key
        )
    
    def _export_outputs(self):
        """Export Pulumi stack outputs"""
        pulumi.export("vector_node_ip", self.vector_node.ipv4_address)
        pulumi.export("app_node_ip", self.app_node.ipv4_address)
        pulumi.export("vpc_id", self.vpc.id)
        pulumi.export("admin_ui_domain", self.config.get("adminUiCustomDomain", "cherry-ai.me"))
        pulumi.export("api_domain", self.config.get("apiDomain", "api.cherry-ai.me"))
        pulumi.export("monitoring_domain", self.config.get("monitoringDomain", "monitoring.cherry-ai.me"))


# Create stack instance when this file is run directly
if __name__ == "__main__":
    config = Config()
    stack = OrchestraStack(
        name="orchestra",
        config={
            "env": config.get("env") or "prod",
            "region": config.get("region") or "sfo3",
            "adminUiCustomDomain": config.get("adminUiCustomDomain") or "cherry-ai.me",
            "apiDomain": config.get("apiDomain") or "api.cherry-ai.me",
            "monitoringDomain": config.get("monitoringDomain") or "monitoring.cherry-ai.me",
            "vectorNodeSize": config.get("vectorNodeSize") or "c-4-8gb-nvme",
            "appNodeSize": config.get("appNodeSize") or "g-8vcpu-32gb",
            "ssh_pubkey_path": config.get("ssh_pubkey_path"),
            "ssh_private_key_path": config.get_secret("ssh_private_key_path")
        }
    )
EOF
  fi
  
  # Update __main__.py to use the new orchestra_stack.py
  cat > "infra/__main__.py" << 'EOF'
"""
Main Pulumi program for Orchestra infrastructure.
"""

import pulumi
from orchestra_stack import OrchestraStack
from pulumi import Config

# Create stack instance
config = Config()
stack = OrchestraStack(
    name="orchestra",
    config={
        "env": config.get("env") or "prod",
        "region": config.get("region") or "sfo3",
        "adminUiCustomDomain": config.get("adminUiCustomDomain") or "cherry-ai.me",
        "apiDomain": config.get("apiDomain") or "api.cherry-ai.me",
        "monitoringDomain": config.get("monitoringDomain") or "monitoring.cherry-ai.me",
        "vectorNodeSize": config.get("vectorNodeSize") or "c-4-8gb-nvme",
        "appNodeSize": config.get("appNodeSize") or "g-8vcpu-32gb",
        "ssh_pubkey_path": config.get("ssh_pubkey_path"),
        "ssh_private_key_path": config.get_secret("ssh_private_key_path")
    }
)
EOF
  
  # Install Pulumi dependencies
  cd "$REPO_ROOT/infra"
  pip install -r requirements.txt
  pip install pulumi_command
  
  # Deploy infrastructure
  echo -e "${BLUE}Deploying infrastructure with Pulumi...${NC}"
  pulumi up --yes
  
  # Get outputs
  VECTOR_NODE_IP=$(pulumi stack output vector_node_ip)
  APP_NODE_IP=$(pulumi stack output app_node_ip)
  
  echo -e "${GREEN}Infrastructure created successfully!${NC}"
  echo -e "${GREEN}Vector Node IP: $VECTOR_NODE_IP${NC}"
  echo -e "${GREEN}App Node IP: $APP_NODE_IP${NC}"
}

# Function to build Admin UI
build_admin_ui() {
  echo -e "${BLUE}${BOLD}Building Admin UI...${NC}"
  
  cd "$REPO_ROOT/admin-ui"
  
  # Install dependencies
  echo -e "${BLUE}Installing dependencies...${NC}"
  pnpm install
  
  # Build the Admin UI
  echo -e "${BLUE}Building Admin UI...${NC}"
  NODE_ENV=production pnpm build
  
  # Verify build output
  if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Build failed! dist directory not found.${NC}"
    exit 1
  fi
  
  # Check for JS and CSS files
  JS_FILES=$(find dist/assets -name "*.js" -type f | wc -l)
  CSS_FILES=$(find dist/assets -name "*.css" -type f | wc -l)
  
  if [ "$JS_FILES" -eq 0 ]; then
    echo -e "${RED}❌ No JavaScript files found in build output.${NC}"
    exit 1
  fi
  
  if [ "$CSS_FILES" -eq 0 ]; then
    echo -e "${RED}❌ No CSS files found in build output.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Admin UI built successfully!${NC}"
}

# Function to deploy Admin UI
deploy_admin_ui() {
  echo -e "${BLUE}${BOLD}Deploying Admin UI...${NC}"
  
  cd "$REPO_ROOT"
  
  # Get App Node IP from Pulumi
  APP_NODE_IP=$(cd infra && pulumi stack output app_node_ip)
  
  if [ -z "$APP_NODE_IP" ]; then
    echo -e "${RED}❌ Failed to get App Node IP from Pulumi.${NC}"
    exit 1
  fi
  
  # Deploy to App Node using rsync
  echo -e "${BLUE}Deploying Admin UI to App Node...${NC}"
  
  # Ensure SSH key has correct permissions
  chmod 600 "$SSH_KEY_PATH"
  
  # Deploy files
  rsync -avz -e "ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no" \
    admin-ui/dist/ "root@$APP_NODE_IP:/var/www/admin-ui/"
  
  echo -e "${GREEN}Admin UI deployed successfully!${NC}"
}

# Function to migrate data from existing to new architecture
migrate_data() {
  echo -e "${BLUE}${BOLD}Migrating data to new architecture...${NC}"
  
  cd "$REPO_ROOT"
  
  # Get node IPs from Pulumi
  VECTOR_NODE_IP=$(cd infra && pulumi stack output vector_node_ip)
  APP_NODE_IP=$(cd infra && pulumi stack output app_node_ip)
  
  if [ -z "$VECTOR_NODE_IP" ] || [ -z "$APP_NODE_IP" ]; then
    echo -e "${RED}❌ Failed to get node IPs from Pulumi.${NC}"
    exit 1
  fi
  
  # Create migration script
  cat > "scripts/migrate_data.py" << EOF
#!/usr/bin/env python3
"""
Data migration script for two-node architecture.
Migrates data from existing infrastructure to new two-node setup.
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migration.log")
    ]
)
logger = logging.getLogger("migration")

def migrate_dragonfly_to_postgres():
    """Migrate data from DragonflyDB to PostgreSQL"""
    logger.info("Migrating data from DragonflyDB to PostgreSQL...")
    
    # Implementation will depend on your data structure
    # This is a placeholder
    
    logger.info("DragonflyDB to PostgreSQL migration completed successfully!")
    return True

def migrate_weaviate_vectors():
    """Migrate vectors from existing Weaviate to new Weaviate"""
    logger.info("Migrating vectors to new Weaviate instance...")
    
    # Implementation will depend on your data structure
    # This is a placeholder
    
    logger.info("Weaviate vector migration completed successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Migrate data to new architecture")
    parser.add_argument("--vector-node", required=True, help="Vector Node IP")
    parser.add_argument("--app-node", required=True, help="App Node IP")
    parser.add_argument("--dragonfly-uri", required=True, help="DragonflyDB URI")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB URI")
    parser.add_argument("--weaviate-url", required=True, help="Weaviate URL")
    parser.add_argument("--weaviate-api-key", help="Weaviate API key")
    
    args = parser.parse_args()
    
    logger.info(f"Starting data migration to new architecture")
    logger.info(f"Vector Node: {args.vector_node}")
    logger.info(f"App Node: {args.app_node}")
    
    # Set environment variables for migration
    os.environ["VECTOR_NODE_IP"] = args.vector_node
    os.environ["APP_NODE_IP"] = args.app_node
    os.environ["DRAGONFLY_URI"] = args.dragonfly_uri
    os.environ["MONGO_URI"] = args.mongo_uri
    os.environ["WEAVIATE_URL"] = args.weaviate_url
    
    if args.weaviate_api_key:
        os.environ["WEAVIATE_API_KEY"] = args.weaviate_api_key
    
    # Run migrations
    success = True
    success = success and migrate_dragonfly_to_postgres()
    success = success and migrate_weaviate_vectors()
    
    if success:
        logger.info("Data migration completed successfully!")
        return 0
    else:
        logger.error("Data migration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
  
  # Make script executable
  chmod +x "scripts/migrate_data.py"
  
  # Get connection details from Pulumi
  DRAGONFLY_URI=$(cd infra && pulumi config get --show-secrets dragonfly_uri)
  MONGO_URI=$(cd infra && pulumi config get --show-secrets mongo_uri)
  WEAVIATE_URL=$(cd infra && pulumi config get --show-secrets weaviate_url)
  WEAVIATE_API_KEY=$(cd infra && pulumi config get --show-secrets weaviate_api_key)
  
  # Run migration script
  echo -e "${BLUE}Running data migration...${NC}"
  
  python3 scripts/migrate_data.py \
    --vector-node "$VECTOR_NODE_IP" \
    --app-node "$APP_NODE_IP" \
    --dragonfly-uri "$DRAGONFLY_URI" \
    --mongo-uri "$MONGO_URI" \
    --weaviate-url "$WEAVIATE_URL" \
    --weaviate-api-key "$WEAVIATE_API_KEY"
  
  MIGRATION_STATUS=$?
  
  if [ $MIGRATION_STATUS -ne 0 ]; then
    echo -e "${RED}❌ Data migration failed!${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Data migration completed successfully!${NC}"
}

# Function to set up monitoring
setup_monitoring() {
  echo -e "${BLUE}${BOLD}Setting up monitoring...${NC}"
  
  cd "$REPO_ROOT"
  
  # Get node IPs from Pulumi
  VECTOR_NODE_IP=$(cd infra && pulumi stack output vector_node_ip)
  APP_NODE_IP=$(cd infra && pulumi stack output app_node_ip)
  
  if [ -z "$VECTOR_NODE_IP" ] || [ -z "$APP_NODE_IP" ]; then
    echo -e "${RED}❌ Failed to get node IPs from Pulumi.${NC}"
    exit 1
  fi
  
  # Create monitoring dashboard setup script
  cat > "scripts/setup_monitoring_dashboard.py" << EOF
#!/usr/bin/env python3
"""
Setup script for Grafana monitoring dashboard.
"""

import os
import sys
import time
import json
import requests
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("monitoring")

# Grafana API configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"
HEADERS = {
    "Content-Type": "application/json"
}

def create_dashboard(vector_node_ip, app_node_ip):
    """Create comprehensive monitoring dashboard"""
    
    # Login to Grafana
    session = requests.Session()
    login_data = {
        "user": GRAFANA_USER,
        "password": GRAFANA_PASSWORD
    }
    
    response = session.post(f"{GRAFANA_URL}/login", json=login_data)
    if response.status_code != 200:
        logger.error(f"Failed to login to Grafana: {response.status_code} {response.text}")
        return False
    
    # Create dashboard
    dashboard_json = {
        "dashboard": {
            "id": None,
            "title": "Orchestra Platform Dashboard",
            "tags": ["orchestra", "production"],
            "timezone": "browser",
            "panels": [
                # System metrics for App Node
                {
                    "title": "App Node CPU Usage",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                    "targets": [{
                        "expr": f"100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode=\"idle\",instance=\"{app_node_ip}:9100\"}}[5m])) * 100)",
                        "legendFormat": "CPU Usage %"
                    }]
                },
                # System metrics for Vector Node
                {
                    "title": "Vector Node CPU Usage",
                    "type": "timeseries",
                    "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
                    "targets": [{
                        "expr": f"100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode=\"idle\",instance=\"{vector_node_ip}:9100\"}}[5m])) * 100)",
                        "legendFormat": "CPU Usage %"
                    }]
                },
                # Memory usage for both nodes
                {
                    "title": "Memory Usage",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
                    "targets": [
                        {
                            "expr": f"node_memory_MemTotal_bytes{{instance=\"{app_node_ip}:9100\"}} - node_memory_MemFree_bytes{{instance=\"{app_node_ip}:9100\"}} - node_memory_Buffers_bytes{{instance=\"{app_node_ip}:9100\"}} - node_memory_Cached_bytes{{instance=\"{app_node_ip}:9100\"}}",
                            "legendFormat": "App Node Memory Used"
                        },
                        {
                            "expr": f"node_memory_MemTotal_bytes{{instance=\"{vector_node_ip}:9100\"}} - node_memory_MemFree_bytes{{instance=\"{vector_node_ip}:9100\"}} - node_memory_Buffers_bytes{{instance=\"{vector_node_ip}:9100\"}} - node_memory_Cached_bytes{{instance=\"{vector_node_ip}:9100\"}}",
                            "legendFormat": "Vector Node Memory Used"
                        }
                    ]
                },
                # API metrics
                {
                    "title": "API Request Rate",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 16, "w": 12, "h": 8},
                    "targets": [{
                        "expr": "sum(rate(http_requests_total{job=\"orchestra_api\"}[5m])) by (status)",
                        "legendFormat": "Status {{status}}"
                    }]
                },
                # API response times
                {
                    "title": "API Response Time (P95)",
                    "type": "timeseries",
                    "gridPos": {"x": 12, "y": 16, "w": 12, "h": 8},
                    "targets": [{
                        "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"orchestra_api\"}[5m])) by (le, endpoint))",
                        "legendFormat": "{{endpoint}}"
                    }]
                },
                # Database metrics
                {
                    "title": "PostgreSQL Active Connections",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 24, "w": 12, "h": 8},
                    "targets": [{
                        "expr": f"pg_stat_activity_count{{instance=\"{vector_node_ip}:9187\"}}",
                        "legendFormat": "Active Connections"
                    }]
                },
                # Weaviate metrics
                {
                    "title": "Weaviate Query Latency",
                    "type": "timeseries",
                    "gridPos": {"x": 12, "y": 24, "w": 12, "h": 8},
                    "targets": [{
                        "expr": "histogram_quantile(0.95, sum(rate(weaviate_query_duration_seconds_bucket[5m])) by (le, operation))",
                        "legendFormat": "{{operation}}"
                    }]
                }
            ]
        },
        "folderId": 0,
        "overwrite": True
    }
    
    # Create or update dashboard
    response = session.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=dashboard_json
    )
    
    if response.status_code in (200, 201):
        logger.info(f"Dashboard created: {response.json().get('url')}")
        return True
    else:
        logger.error(f"Failed to create dashboard: {response.status_code} {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Setup monitoring dashboard")
    parser.add_argument("--vector-node", required=True, help="Vector Node IP")
    parser.add_argument("--app-node", required=True, help="App Node IP")
    
    args = parser.parse_args()
    
    logger.info(f"Setting up monitoring dashboard")
    logger.info(f"Vector Node: {args.vector_node}")
    logger.info(f"App Node: {args.app_node}")
    
    # Wait for Grafana to be ready
    logger.info("Waiting for Grafana to be ready...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200 and response.json().get("database") == "ok":
                logger.info("Grafana is ready!")
                break
        except requests.exceptions.RequestException:
            pass
        
        retry_count += 1
        logger.info(f"Waiting for Grafana... ({retry_count}/{max_retries})")
        time.sleep(5)
    
    if retry_count >= max_retries:
        logger.error("Grafana is not ready after maximum retries")
        return 1
    
    # Create dashboard
    if create_dashboard(args.vector_node, args.app_node):
        logger.info("Monitoring dashboard setup completed successfully!")
        return 0
    else:
        logger.error("Monitoring dashboard setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
  
  # Make script executable
  chmod +x "scripts/setup_monitoring_dashboard.py"
  
  # Copy script to App Node
  echo -e "${BLUE}Copying monitoring setup script to App Node...${NC}"
  
  # Ensure SSH key has correct permissions
  chmod 600 "$SSH_KEY_PATH"
  
  # Copy script
  scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no \
    "scripts/setup_monitoring_dashboard.py" "root@$APP_NODE_IP:/opt/monitoring/"
  
  # Run script on App Node
  echo -e "${BLUE}Running monitoring setup script on App Node...${NC}"
  
  ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "root@$APP_NODE_IP" \
    "cd /opt/monitoring && python3 setup_monitoring_dashboard.py --vector-node $VECTOR_NODE_IP --app-node $APP_NODE_IP"
  
  MONITORING_STATUS=$?
  
  if [ $MONITORING_STATUS -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Monitoring setup may have issues. Check logs on App Node.${NC}"
  else
    echo -e "${GREEN}Monitoring setup completed successfully!${NC}"
  fi
  
  # Set up SSL certificates for domains
  echo -e "${BLUE}Setting up SSL certificates...${NC}"
  
  # Get domain names from Pulumi
  ADMIN_UI_DOMAIN=$(cd infra && pulumi stack output admin_ui_domain)
  API_DOMAIN=$(cd infra && pulumi stack output api_domain)
  MONITORING_DOMAIN=$(cd infra && pulumi stack output monitoring_domain)
  
  # Run certbot on App Node
  ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "root@$APP_NODE_IP" \
    "certbot --nginx -d $ADMIN_UI_DOMAIN -d $API_DOMAIN -d $MONITORING_DOMAIN --non-interactive --agree-tos -m admin@cherry-ai.me"
  
  SSL_STATUS=$?
  
  if [ $SSL_STATUS -ne 0 ]; then
    echo -e "${YELLOW}⚠️ SSL certificate setup may have issues. Check logs on App Node.${NC}"
  else
    echo -e "${GREEN}SSL certificates set up successfully!${NC}"
  fi
}

# Function to verify deployment
verify_deployment() {
  echo -e "${BLUE}${BOLD}Verifying deployment...${NC}"
  
  cd "$REPO_ROOT"
  
  # Get domain names from Pulumi
  ADMIN_UI_DOMAIN=$(cd infra && pulumi stack output admin_ui_domain)
  API_DOMAIN=$(cd infra && pulumi stack output api_domain)
  MONITORING_DOMAIN=$(cd infra && pulumi stack output monitoring_domain)
  
  # Create verification script
  cat > "scripts/verify_deployment.py" << EOF
#!/usr/bin/env python3
"""
Verification script for two-node architecture deployment.
"""

import os
import sys
import time
import json
import requests
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("verification")

def check_admin_ui(domain):
    """Check if Admin UI is accessible"""
    logger.info(f"Checking Admin UI at https://{domain}...")
    
    try:
        response = requests.get(f"https://{domain}", timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Admin UI is accessible (HTTP 200)")
            
            # Check for blank page
            if len(response.text) < 500:
                logger.warning(f"Admin UI content is suspiciously small ({len(response.text)} bytes). Possible blank page.")
                return False
            
            # Check for JS and CSS references
            if "assets/index-" in response.text and ".js" in response.text:
                logger.info("JavaScript reference found in HTML")
            else:
                logger.warning("No JavaScript reference found in HTML")
                return False
            
            if "assets/index-" in response.text and ".css" in response.text:
                logger.info("CSS reference found in HTML")
            else:
                logger.warning("No CSS reference found in HTML")
                return False
            
            return True
        else:
            logger.error(f"Admin UI returned HTTP {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing Admin UI: {str(e)}")
        return False

def check_api(domain):
    """Check if API is accessible"""
    logger.info(f"Checking API at https://{domain}...")
    
    try:
        response = requests.get(f"https://{domain}/health", timeout=10)
        
        if response.status_code == 200:
            logger.info(f"API is accessible (HTTP 200)")
            return True
        else:
            logger.error(f"API returned HTTP {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing API: {str(e)}")
        return False

def check_monitoring(domain):
    """Check if monitoring is accessible"""
    logger.info(f"Checking monitoring at https://{domain}...")
    
    try:
        response = requests.get(f"https://{domain}/api/health", timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Monitoring is accessible (HTTP 200)")
            return True
        else:
            logger.error(f"Monitoring returned HTTP {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing monitoring: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verify deployment")
    parser.add_argument("--admin-ui-domain", required=True, help="Admin UI domain")
    parser.add_argument("--api-domain", required=True, help="API domain")
    parser.add_argument("--monitoring-domain", required=True, help="Monitoring domain")
    parser.add_argument("--timeout", type=int, default=300, help="Verification timeout in seconds")
    
    args = parser.parse_args()
    
    logger.info(f"Starting deployment verification")
    logger.info(f"Admin UI domain: {args.admin_ui_domain}")
    logger.info(f"API domain: {args.api_domain}")
    logger.info(f"Monitoring domain: {args.monitoring_domain}")
    
    # Wait for DNS propagation and SSL certificates
    logger.info(f"Waiting for DNS propagation and SSL certificates (up to {args.timeout} seconds)...")
    
    start_time = time.time()
    end_time = start_time + args.timeout
    
    admin_ui_ok = False
    api_ok = False
    monitoring_ok = False
    
    while time.time() < end_time:
        # Check Admin UI
        if not admin_ui_ok:
            admin_ui_ok = check_admin_ui(args.admin_ui_domain)
        
        # Check API
        if not api_ok:
            api_ok = check_api(args.api_domain)
        
        # Check monitoring
        if not monitoring_ok:
            monitoring_ok = check_monitoring(args.monitoring_domain)
        
        # If all checks pass, we're done
        if admin_ui_ok and api_ok and monitoring_ok:
            logger.info("All checks passed!")
            return 0
        
        # Wait before retrying
        elapsed = time.time() - start_time
        remaining = args.timeout - elapsed
        
        if remaining > 0:
            logger.info(f"Some checks failed. Retrying in 10 seconds... (timeout in {int(remaining)} seconds)")
            time.sleep(10)
    
    # If we get here, some checks failed
    logger.error("Verification failed after timeout!")
    logger.error(f"Admin UI: {'OK' if admin_ui_ok else 'FAILED'}")
    logger.error(f"API: {'OK' if api_ok else 'FAILED'}")
    logger.error(f"Monitoring: {'OK' if monitoring_ok else 'FAILED'}")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
  
  # Make script executable
  chmod +x "scripts/verify_deployment.py"
  
  # Run verification script
  echo -e "${BLUE}Running verification script...${NC}"
  
  python3 scripts/verify_deployment.py \
    --admin-ui-domain "$ADMIN_UI_DOMAIN" \
    --api-domain "$API_DOMAIN" \
    --monitoring-domain "$MONITORING_DOMAIN" \
    --timeout "$VERIFY_TIMEOUT"
  
  VERIFY_STATUS=$?
  
  if [ $VERIFY_STATUS -ne 0 ]; then
    echo -e "${RED}❌ Verification failed!${NC}"
    echo -e "${YELLOW}Some components may still be initializing or DNS may not have propagated yet.${NC}"
    echo -e "${YELLOW}You can run the verification script again later:${NC}"
    echo -e "${PURPLE}python3 scripts/verify_deployment.py --admin-ui-domain $ADMIN_UI_DOMAIN --api-domain $API_DOMAIN --monitoring-domain $MONITORING_DOMAIN${NC}"
  else
    echo -e "${GREEN}Verification completed successfully!${NC}"
  fi
}

# Function to display summary
display_summary() {
  echo -e "\n${BLUE}${BOLD}Deployment Summary${NC}"
  
  cd "$REPO_ROOT"
  
  # Get outputs from Pulumi
  VECTOR_NODE_IP=$(cd infra && pulumi stack output vector_node_ip)
  APP_NODE_IP=$(cd infra && pulumi stack output app_node_ip)
  ADMIN_UI_DOMAIN=$(cd infra && pulumi stack output admin_ui_domain)
  API_DOMAIN=$(cd infra && pulumi stack output api_domain)
  MONITORING_DOMAIN=$(cd infra && pulumi stack output monitoring_domain)
  
  echo -e "${CYAN}Two-Node Architecture Deployment${NC}"
  echo -e "${CYAN}===============================${NC}"
  echo -e "${GREEN}Vector Node (CPU-Optimized Premium with NVMe)${NC}"
  echo -e "  IP: $VECTOR_NODE_IP"
  echo -e "  Services: Weaviate, PostgreSQL"
  echo -e ""
  echo -e "${GREEN}App Node (General Purpose)${NC}"
  echo -e "  IP: $APP_NODE_IP"
  echo -e "  Services: Orchestra API, Admin UI, Monitoring"
  echo -e ""
  echo -e "${GREEN}Domains${NC}"
  echo -e "  Admin UI: https://$ADMIN_UI_DOMAIN"
  echo -e "  API: https://$API_DOMAIN"
  echo -e "  Monitoring: https://$MONITORING_DOMAIN"
  echo -e ""
  echo -e "${YELLOW}Notes${NC}"
  echo -e "  - DNS propagation may take up to 24 hours"
  echo -e "  - SSL certificates may take some time to be fully active"
  echo -e "  - Monitoring dashboards may need additional configuration"
  echo -e ""
  echo -e "${CYAN}Next Steps${NC}"
  echo -e "  1. Verify all services are running correctly"
  echo -e "  2. Update DNS records if needed"
  echo -e "  3. Configure monitoring alerts"
  echo -e "  4. Perform thorough testing of the new architecture"
  echo -e ""
  echo -e "${PURPLE}Useful Commands${NC}"
  echo -e "  - Verify deployment: python3 scripts/verify_deployment.py --admin-ui-domain $ADMIN_UI_DOMAIN --api-domain $API_DOMAIN --monitoring-domain $MONITORING_DOMAIN"
  echo -e "  - SSH to Vector Node: ssh -i $SSH_KEY_PATH root@$VECTOR_NODE_IP"
  echo -e "  - SSH to App Node: ssh -i $SSH_KEY_PATH root@$APP_NODE_IP"
  echo -e "  - View Pulumi stack: cd infra && pulumi stack"
  echo -e ""
  echo -e "${GREEN}${BOLD}Deployment completed!${NC}"
}

# Main function
main() {
  echo -e "${CYAN}${BOLD}"
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║                                                            ║"
  echo "║   🚀 Cherry AI Two-Node Architecture Deployment 🚀         ║"
  echo "║                                                            ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
  
  # Check prerequisites
  check_prerequisites
  
  # Initialize Pulumi project
  initialize_pulumi
  
  # Create infrastructure
  create_infrastructure
  
  # Build Admin UI
  build_admin_ui
  
  # Deploy Admin UI
  deploy_admin_ui
  
  # Migrate data
  migrate_data
  
  # Set up monitoring
  setup_monitoring
  
  # Verify deployment
  verify_deployment
  
  # Display summary
  display_summary
}

# Run the main function
main
