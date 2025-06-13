"""
Lambda Labs Infrastructure Setup for Orchestra AI
Pulumi Infrastructure as Code Configuration
"""

import pulumi
import pulumi_command as command
import json
import base64

# Configuration
config = pulumi.Config()
lambda_api_key = "secret_pulumi_87a092f03b5e4896a56542ed6e07d249.bHCTOCe4mkvm9jiT53DWZpnewReAoGic"
ssh_public_key = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDMQ+BMDckhfiutxjpFUxtMwLnGHkDyI/oh4mQ76oudkjptAJfywKYCR+ShUM1HbuNdCGJJEbfTV6f85Mhwn2y+Qktxi0T550N/afX3lqZiXTCrIPUJrAq1hgFQJCDLi8aSU7KHLilB9fxIdLy5vNPKaAculG83VS43QayPK15r8KslyyKBBdCZhzSncmQdabTW48QtyO3NjH1lX7XXCL3AHi7KR1ES8YcPMpUla1IOqLKw/pRaDrwLkNdrkTEW/PE+RnpNVSw4CiFtqi/D0WSTaovwIHVQAIeIGMjtIEi47Jalgy3bgH4uSChSdhja5LxCuMsVnK1OeHLnMmf/rS6L7/72amviJU1oS8Y7l1Y5UnalfF8dmkheexvoQL4M2z9BmO0Ak9apT2cawzif0HtZoFJWeeLzuBLkOgtyGP4iYQoFp2ofkU3ze/i0R2hySh/FqVnAsB0Fn95gaXCNHhGrVCsbxQQBDDKkE6oLFg/vgkgAwJfgAMphdCqaoFCrjyp+yIZbvqwj79BihZEIzk1WtZYpOCRHOVSQC5caOW+wvYBDwjscidgSsmNVEZWpZzoK4vo9Ne5G5imJL8DVm4gqhmNgcJjylVV+wePdBAq+Ev3NEEoV0343DaTmQzXlGrcsEB/cmvPHPDhpJNwP7ySR9o10MibyMQJBmdPiOy+c5w== manus-ai-deployment"""

# Lambda Labs API helper functions
def create_lambda_instance(name: str, instance_type: str, region: str, ssh_key_name: str):
    """Create a Lambda Labs GPU instance"""
    
    # Create SSH key first
    ssh_key_creation = command.local.Command(
        f"create-ssh-key-{ssh_key_name}",
        create=f"""
        curl -X POST https://cloud.lambda.ai/api/v1/ssh-keys \\
        -u {lambda_api_key}: \\
        -H "Content-Type: application/json" \\
        -d '{{"name": "{ssh_key_name}", "public_key": "{ssh_public_key}"}}'
        """,
        opts=pulumi.ResourceOptions(ignore_changes=["create"])
    )
    
    # Create the instance
    instance_creation = command.local.Command(
        f"create-instance-{name}",
        create=f"""
        curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/launch \\
        -u {lambda_api_key}: \\
        -H "Content-Type: application/json" \\
        -d '{{"region_name": "{region}", "instance_type_name": "{instance_type}", "ssh_key_names": ["{ssh_key_name}"], "name": "{name}"}}'
        """,
        delete=f"""
        # Get instance ID and terminate
        INSTANCE_ID=$(curl -s -u {lambda_api_key}: https://cloud.lambda.ai/api/v1/instances | jq -r '.data[] | select(.name=="{name}") | .id')
        if [ "$INSTANCE_ID" != "null" ] && [ "$INSTANCE_ID" != "" ]; then
            curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/terminate \\
            -u {lambda_api_key}: \\
            -H "Content-Type: application/json" \\
            -d '{{"instance_ids": ["'$INSTANCE_ID'"]}}'
        fi
        """,
        opts=pulumi.ResourceOptions(depends_on=[ssh_key_creation])
    )
    
    return instance_creation

# Infrastructure Components

# 1. K3s Master Node (A10 for cost efficiency)
k3s_master = create_lambda_instance(
    name="orchestra-k3s-master",
    instance_type="gpu_1x_a10",
    region="us-west-1",
    ssh_key_name="manus-ai-deployment"
)

# 2. MCP Server Node (A100 for AI workloads)
mcp_server = create_lambda_instance(
    name="orchestra-mcp-server",
    instance_type="gpu_1x_a100_sxm4",
    region="us-east-1",
    ssh_key_name="manus-ai-deployment"
)

# 3. Vector Database Node (A6000 for large memory)
vector_db = create_lambda_instance(
    name="orchestra-vector-db",
    instance_type="gpu_1x_a6000",
    region="us-west-1",
    ssh_key_name="manus-ai-deployment"
)

# Setup scripts for each instance
k3s_setup_script = """#!/bin/bash
# K3s Master Setup Script
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install K3s
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# Install Portainer
kubectl apply -n portainer -f https://downloads.portainer.io/ce2-19/portainer.yaml

# Install NVIDIA device plugin
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Setup firewall
ufw allow 22/tcp
ufw allow 6443/tcp
ufw allow 9443/tcp
ufw --force enable

echo "K3s master setup complete!"
echo "Portainer will be available at: https://$(curl -s ifconfig.me):9443"
echo "K3s token: $(cat /var/lib/rancher/k3s/server/node-token)"
"""

mcp_setup_script = """#!/bin/bash
# MCP Server Setup Script
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install NVIDIA drivers and CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update && apt-get install -y nvidia-docker2
systemctl restart docker

# Clone Orchestra AI repository
cd /opt
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup systemd services for MCP servers
cat > /etc/systemd/system/orchestra-mcp.service << EOF
[Unit]
Description=Orchestra AI MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/orchestra-main
Environment=PATH=/opt/orchestra-main/venv/bin
ExecStart=/opt/orchestra-main/venv/bin/python main_mcp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable orchestra-mcp
systemctl start orchestra-mcp

echo "MCP server setup complete!"
"""

vector_db_setup_script = """#!/bin/bash
# Vector Database Setup Script
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install NVIDIA drivers
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda

# Setup Weaviate with GPU support
mkdir -p /opt/weaviate
cd /opt/weaviate

cat > docker-compose.yml << EOF
version: '3.4'
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8080'
    - --scheme
    - http
    image: semitechnologies/weaviate:1.22.4
    ports:
    - "8080:8080"
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
      ENABLE_MODULES: 'text2vec-transformers'
      TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
    - weaviate_data:/var/lib/weaviate
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
volumes:
  weaviate_data:
EOF

docker-compose up -d

# Setup PostgreSQL for metadata
docker run -d \\
  --name postgres \\
  -e POSTGRES_PASSWORD=orchestra_ai_2024 \\
  -e POSTGRES_DB=orchestra \\
  -p 5432:5432 \\
  -v postgres_data:/var/lib/postgresql/data \\
  postgres:15

echo "Vector database setup complete!"
echo "Weaviate available at: http://$(curl -s ifconfig.me):8080"
echo "PostgreSQL available at: $(curl -s ifconfig.me):5432"
"""

# Deploy setup scripts to instances
k3s_setup = command.remote.Command(
    "k3s-setup",
    connection=command.remote.ConnectionArgs(
        host=k3s_master.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu",
        private_key=config.require_secret("ssh_private_key")
    ),
    create=k3s_setup_script,
    opts=pulumi.ResourceOptions(depends_on=[k3s_master])
)

mcp_setup = command.remote.Command(
    "mcp-setup",
    connection=command.remote.ConnectionArgs(
        host=mcp_server.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu",
        private_key=config.require_secret("ssh_private_key")
    ),
    create=mcp_setup_script,
    opts=pulumi.ResourceOptions(depends_on=[mcp_server])
)

vector_setup = command.remote.Command(
    "vector-setup",
    connection=command.remote.ConnectionArgs(
        host=vector_db.stdout.apply(lambda x: json.loads(x)["data"]["ip"]),
        user="ubuntu",
        private_key=config.require_secret("ssh_private_key")
    ),
    create=vector_db_setup_script,
    opts=pulumi.ResourceOptions(depends_on=[vector_db])
)

# Outputs
pulumi.export("k3s_master_ip", k3s_master.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))
pulumi.export("mcp_server_ip", mcp_server.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))
pulumi.export("vector_db_ip", vector_db.stdout.apply(lambda x: json.loads(x)["data"]["ip"]))
pulumi.export("portainer_url", k3s_master.stdout.apply(lambda x: f"https://{json.loads(x)['data']['ip']}:9443"))
pulumi.export("weaviate_url", vector_db.stdout.apply(lambda x: f"http://{json.loads(x)['data']['ip']}:8080"))

