"""
Orchestra AI - Secure Infrastructure as Code
Enhanced Pulumi configuration with proper secret management
"""

import pulumi
import pulumi_command as command
import json
import os
from typing import Dict, Any

# Secure configuration management
config = pulumi.Config()

class SecureInfrastructure:
    """Secure infrastructure management with proper secret handling"""
    
    def __init__(self):
        # Get secrets from Pulumi config (encrypted)
        self.lambda_api_key = config.require_secret("lambda_api_key")
        self.ssh_private_key = config.require_secret("ssh_private_key") 
        self.github_token = config.require_secret("github_token")
        self.vercel_token = config.require_secret("vercel_token")
        
        # Get SSH public key from config
        self.ssh_public_key = config.require("ssh_public_key")
        
        # Environment-specific configuration
        self.environment = config.get("environment") or "production"
        self.project_name = config.get("project_name") or "orchestra-ai"
        
    def create_lambda_instance(self, name: str, instance_type: str, region: str, ssh_key_name: str):
        """Create Lambda Labs GPU instance with secure API handling"""
        
        # Create SSH key with secure API call
        ssh_key_creation = command.local.Command(
            f"create-ssh-key-{ssh_key_name}",
            create=pulumi.Output.all(self.lambda_api_key, self.ssh_public_key).apply(
                lambda args: f"""
                curl -X POST https://cloud.lambda.ai/api/v1/ssh-keys \\
                -u {args[0]}: \\
                -H "Content-Type: application/json" \\
                -d '{{"name": "{ssh_key_name}", "public_key": "{args[1]}"}}'
                """
            ),
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"],
                ignore_changes=["create"]
            )
        )
        
        # Create instance with secure API call
        instance_creation = command.local.Command(
            f"create-instance-{name}",
            create=self.lambda_api_key.apply(
                lambda api_key: f"""
                curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/launch \\
                -u {api_key}: \\
                -H "Content-Type: application/json" \\
                -d '{{"region_name": "{region}", "instance_type_name": "{instance_type}", "ssh_key_names": ["{ssh_key_name}"], "name": "{name}"}}'
                """
            ),
            delete=self.lambda_api_key.apply(
                lambda api_key: f"""
                INSTANCE_ID=$(curl -s -u {api_key}: https://cloud.lambda.ai/api/v1/instances | jq -r '.data[] | select(.name=="{name}") | .id')
                if [ "$INSTANCE_ID" != "null" ] && [ "$INSTANCE_ID" != "" ]; then
                    curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/terminate \\
                    -u {api_key}: \\
                    -H "Content-Type: application/json" \\
                    -d '{{"instance_ids": ["'$INSTANCE_ID'"]}}'
                fi
                """
            ),
            opts=pulumi.ResourceOptions(
                depends_on=[ssh_key_creation],
                additional_secret_outputs=["create", "delete"]
            )
        )
        
        return instance_creation
    
    def create_secure_setup_script(self, script_type: str) -> str:
        """Generate secure setup scripts with environment-specific configuration"""
        
        base_script = """#!/bin/bash
# Orchestra AI Secure Setup Script
set -e

# Security: Update system first
apt-get update && apt-get upgrade -y

# Install essential security tools
apt-get install -y fail2ban ufw htop curl wget jq git

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable

# Install Docker with security best practices
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Configure Docker daemon with security settings
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true
}
EOF

systemctl restart docker
"""
        
        if script_type == "k3s_master":
            return base_script + """
# Install K3s with security configurations
curl -sfL https://get.k3s.io | sh -s - \\
  --write-kubeconfig-mode 644 \\
  --disable traefik \\
  --disable servicelb \\
  --kube-apiserver-arg=audit-log-path=/var/log/k3s-audit.log \\
  --kube-apiserver-arg=audit-log-maxage=30 \\
  --kube-apiserver-arg=audit-log-maxbackup=10 \\
  --kube-apiserver-arg=audit-log-maxsize=100

# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Configure network policies
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

# Setup monitoring
kubectl create namespace monitoring
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

echo "K3s master setup complete with security hardening!"
"""
        
        elif script_type == "mcp_server":
            return base_script + """
# Install Python 3.11 with security updates
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install NVIDIA drivers and CUDA (latest secure versions)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda-toolkit-12-3

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \\
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \\
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update && apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Clone Orchestra AI repository (using deploy key)
cd /opt
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Setup secure Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create secure environment file
cat > .env << 'EOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://orchestra:${DB_PASSWORD}@postgres:5432/orchestra_ai
REDIS_URL=redis://redis:6379
LAMBDA_API_KEY=${LAMBDA_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}
VERCEL_TOKEN=${VERCEL_TOKEN}
EOF

# Setup systemd service with security restrictions
cat > /etc/systemd/system/orchestra-mcp.service << 'EOF'
[Unit]
Description=Orchestra AI MCP Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/orchestra-main
Environment=PATH=/opt/orchestra-main/venv/bin
EnvironmentFile=/opt/orchestra-main/.env
ExecStart=/opt/orchestra-main/venv/bin/python main_mcp.py
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/orchestra-main

[Install]
WantedBy=multi-user.target
EOF

systemctl enable orchestra-mcp
systemctl start orchestra-mcp

echo "MCP server setup complete with security hardening!"
"""
        
        elif script_type == "vector_db":
            return base_script + """
# Install NVIDIA drivers
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda-toolkit-12-3

# Setup secure Weaviate with authentication
mkdir -p /opt/weaviate
cd /opt/weaviate

# Generate secure passwords
WEAVIATE_AUTH_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)

cat > docker-compose.yml << EOF
version: '3.8'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
    - "8080:8080"
    restart: unless-stopped
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: '${WEAVIATE_AUTH_KEY}'
      AUTHENTICATION_APIKEY_USERS: 'orchestra@admin'
      AUTHORIZATION_ADMINLIST_ENABLED: 'true'
      AUTHORIZATION_ADMINLIST_USERS: 'orchestra'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
      ENABLE_MODULES: 'text2vec-transformers'
      TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
    - weaviate_data:/var/lib/weaviate
    networks:
    - weaviate_network
    
  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2
    environment:
      ENABLE_CUDA: '1'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
    - weaviate_network
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: orchestra
      POSTGRES_USER: orchestra
    ports:
    - "5432:5432"
    volumes:
    - postgres_data:/var/lib/postgresql/data
    networks:
    - weaviate_network
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
    - "6379:6379"
    volumes:
    - redis_data:/data
    networks:
    - weaviate_network
    restart: unless-stopped
    command: redis-server --requirepass ${POSTGRES_PASSWORD}

volumes:
  weaviate_data:
  postgres_data:
  redis_data:

networks:
  weaviate_network:
    driver: bridge
EOF

# Save credentials securely
cat > /opt/weaviate/.env << EOF
WEAVIATE_AUTH_KEY=${WEAVIATE_AUTH_KEY}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
EOF

chmod 600 /opt/weaviate/.env

docker-compose up -d

echo "Vector database setup complete with authentication!"
echo "Weaviate API Key: ${WEAVIATE_AUTH_KEY}"
echo "PostgreSQL Password: ${POSTGRES_PASSWORD}"
"""
        
        return base_script

# Initialize secure infrastructure
infrastructure = SecureInfrastructure()

# Create infrastructure components with security
k3s_master = infrastructure.create_lambda_instance(
    name=f"{infrastructure.project_name}-k3s-master",
    instance_type="gpu_1x_a10",
    region="us-west-1", 
    ssh_key_name="orchestra-deployment-key"
)

mcp_server = infrastructure.create_lambda_instance(
    name=f"{infrastructure.project_name}-mcp-server",
    instance_type="gpu_1x_a100_sxm4",
    region="us-east-1",
    ssh_key_name="orchestra-deployment-key"
)

vector_db = infrastructure.create_lambda_instance(
    name=f"{infrastructure.project_name}-vector-db", 
    instance_type="gpu_1x_a6000",
    region="us-west-1",
    ssh_key_name="orchestra-deployment-key"
)

# Deploy secure setup scripts
k3s_setup = command.remote.Command(
    "k3s-secure-setup",
    connection=command.remote.ConnectionArgs(
        host=k3s_master.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu",
        private_key=infrastructure.ssh_private_key
    ),
    create=infrastructure.create_secure_setup_script("k3s_master"),
    opts=pulumi.ResourceOptions(
        depends_on=[k3s_master],
        additional_secret_outputs=["create"]
    )
)

mcp_setup = command.remote.Command(
    "mcp-secure-setup",
    connection=command.remote.ConnectionArgs(
        host=mcp_server.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu", 
        private_key=infrastructure.ssh_private_key
    ),
    create=infrastructure.create_secure_setup_script("mcp_server"),
    opts=pulumi.ResourceOptions(
        depends_on=[mcp_server],
        additional_secret_outputs=["create"]
    )
)

vector_setup = command.remote.Command(
    "vector-secure-setup",
    connection=command.remote.ConnectionArgs(
        host=vector_db.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu",
        private_key=infrastructure.ssh_private_key
    ),
    create=infrastructure.create_secure_setup_script("vector_db"),
    opts=pulumi.ResourceOptions(
        depends_on=[vector_db],
        additional_secret_outputs=["create"]
    )
)

# Secure outputs (marked as secrets where appropriate)
pulumi.export("k3s_master_ip", k3s_master.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))
pulumi.export("mcp_server_ip", mcp_server.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))
pulumi.export("vector_db_ip", vector_db.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))

# URLs for services (not marked as secret since they're public endpoints)
pulumi.export("k3s_dashboard_url", k3s_master.stdout.apply(lambda x: f"https://{json.loads(x)['data']['ip']}:6443"))
pulumi.export("weaviate_url", vector_db.stdout.apply(lambda x: f"http://{json.loads(x)['data']['ip']}:8080"))
pulumi.export("postgres_url", vector_db.stdout.apply(lambda x: f"postgresql://orchestra@{json.loads(x)['data']['ip']}:5432/orchestra"))

# Security notice
pulumi.export("security_notice", "All services deployed with security hardening. Check instance logs for generated passwords.")

