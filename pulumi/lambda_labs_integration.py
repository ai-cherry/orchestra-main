"""
Orchestra AI - Enhanced Lambda Labs Integration with Pulumi Custom Resources
Implements user's IaC strategy for GPU compute management
"""

import pulumi
import pulumi_command as command
import json
import requests
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import enhanced secret manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from security.enhanced_secret_manager import secret_manager

class LambdaLabsCustomResource(pulumi.CustomResource):
    """Custom Pulumi resource for Lambda Labs GPU instances"""
    
    def __init__(self, name: str, props: Dict[str, Any], opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__("orchestra:lambda:Instance", name, props, opts)

class LambdaLabsProvider:
    """Lambda Labs provider for Pulumi using Custom Resources and Dynamic Providers"""
    
    def __init__(self):
        self.api_key = secret_manager.get_secret("LAMBDA_API_KEY")
        self.base_url = "https://cloud.lambda.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("LAMBDA_API_KEY is required for Lambda Labs integration")
    
    def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request to Lambda Labs"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=(self.api_key, ""),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            pulumi.log.error(f"Lambda Labs API request failed: {str(e)}")
            raise
    
    def list_instance_types(self) -> List[Dict[str, Any]]:
        """List available instance types"""
        return self._make_api_request("GET", "instance-types")
    
    def list_regions(self) -> List[Dict[str, Any]]:
        """List available regions"""
        return self._make_api_request("GET", "regions")
    
    def create_ssh_key(self, name: str, public_key: str) -> Dict[str, Any]:
        """Create SSH key for instance access"""
        data = {
            "name": name,
            "public_key": public_key
        }
        return self._make_api_request("POST", "ssh-keys", data)
    
    def launch_instance(self, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch a new GPU instance"""
        return self._make_api_request("POST", "instance-operations/launch", instance_config)
    
    def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an instance"""
        data = {"instance_ids": [instance_id]}
        return self._make_api_request("POST", "instance-operations/terminate", data)
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get instance status"""
        instances = self._make_api_request("GET", "instances")
        for instance in instances.get("data", []):
            if instance["id"] == instance_id:
                return instance
        return {}

class LambdaLabsDynamicProvider(pulumi.dynamic.ResourceProvider):
    """Dynamic provider for Lambda Labs instances"""
    
    def __init__(self):
        self.provider = LambdaLabsProvider()
    
    def create(self, props):
        """Create a new Lambda Labs instance"""
        try:
            # Extract configuration
            instance_name = props["name"]
            instance_type = props["instance_type"]
            region = props["region"]
            ssh_key_name = props["ssh_key_name"]
            ssh_public_key = props.get("ssh_public_key")
            
            # Create SSH key if provided
            if ssh_public_key:
                try:
                    self.provider.create_ssh_key(ssh_key_name, ssh_public_key)
                    pulumi.log.info(f"Created SSH key: {ssh_key_name}")
                except Exception as e:
                    pulumi.log.warn(f"SSH key creation failed (may already exist): {str(e)}")
            
            # Launch instance
            instance_config = {
                "region_name": region,
                "instance_type_name": instance_type,
                "ssh_key_names": [ssh_key_name],
                "name": instance_name
            }
            
            result = self.provider.launch_instance(instance_config)
            instance_id = result["data"]["instance_ids"][0]
            
            # Wait for instance to be running
            self._wait_for_instance_running(instance_id)
            
            # Get instance details
            instance_details = self.provider.get_instance_status(instance_id)
            
            outputs = {
                "id": instance_id,
                "name": instance_name,
                "ip": instance_details.get("ip"),
                "status": instance_details.get("status"),
                "instance_type": instance_type,
                "region": region
            }
            
            return pulumi.dynamic.CreateResult(
                id_=instance_id,
                outs=outputs
            )
            
        except Exception as e:
            pulumi.log.error(f"Failed to create Lambda Labs instance: {str(e)}")
            raise
    
    def delete(self, id_, props):
        """Delete a Lambda Labs instance"""
        try:
            self.provider.terminate_instance(id_)
            pulumi.log.info(f"Terminated Lambda Labs instance: {id_}")
        except Exception as e:
            pulumi.log.error(f"Failed to terminate instance {id_}: {str(e)}")
            # Don't raise exception to allow Pulumi to continue cleanup
    
    def update(self, id_, old_props, new_props):
        """Update a Lambda Labs instance (limited support)"""
        # Lambda Labs doesn't support instance updates, so we return current state
        instance_details = self.provider.get_instance_status(id_)
        
        outputs = {
            "id": id_,
            "name": new_props["name"],
            "ip": instance_details.get("ip"),
            "status": instance_details.get("status"),
            "instance_type": new_props["instance_type"],
            "region": new_props["region"]
        }
        
        return pulumi.dynamic.UpdateResult(outs=outputs)
    
    def _wait_for_instance_running(self, instance_id: str, timeout: int = 300):
        """Wait for instance to reach running state"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            instance = self.provider.get_instance_status(instance_id)
            status = instance.get("status", "unknown")
            
            if status == "running":
                pulumi.log.info(f"Instance {instance_id} is running")
                return
            elif status in ["terminated", "error"]:
                raise Exception(f"Instance {instance_id} failed to start: {status}")
            
            pulumi.log.info(f"Waiting for instance {instance_id} to start (current status: {status})")
            time.sleep(10)
        
        raise Exception(f"Instance {instance_id} did not start within {timeout} seconds")

class LambdaLabsInstance(pulumi.dynamic.Resource):
    """Lambda Labs GPU instance resource"""
    
    def __init__(self, name: str, args: Dict[str, Any], opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(LambdaLabsDynamicProvider(), name, args, opts)

class LambdaLabsInfrastructure:
    """Complete Lambda Labs infrastructure management"""
    
    def __init__(self):
        self.provider = LambdaLabsProvider()
        self.ssh_public_key = secret_manager.get_secret("SSH_PUBLIC_KEY")
        self.ssh_private_key = secret_manager.get_secret("SSH_PRIVATE_KEY")
        
    def create_orchestra_cluster(self) -> Dict[str, LambdaLabsInstance]:
        """Create complete Orchestra AI cluster on Lambda Labs"""
        
        instances = {}
        
        # API Server Instance (A100 for heavy AI workloads)
        api_server = LambdaLabsInstance(
            "orchestra-api-server",
            {
                "name": "orchestra-api-server",
                "instance_type": "gpu_1x_a100_sxm4",
                "region": "us-east-1",
                "ssh_key_name": "orchestra-deployment-key",
                "ssh_public_key": self.ssh_public_key
            },
            opts=pulumi.ResourceOptions(
                protect=True  # Protect production instances
            )
        )
        instances["api_server"] = api_server
        
        # MCP Server Instance (A10 for MCP operations)
        mcp_server = LambdaLabsInstance(
            "orchestra-mcp-server",
            {
                "name": "orchestra-mcp-server", 
                "instance_type": "gpu_1x_a10",
                "region": "us-west-1",
                "ssh_key_name": "orchestra-deployment-key",
                "ssh_public_key": self.ssh_public_key
            }
        )
        instances["mcp_server"] = mcp_server
        
        # Vector Database Instance (A6000 for vector operations)
        vector_db = LambdaLabsInstance(
            "orchestra-vector-db",
            {
                "name": "orchestra-vector-db",
                "instance_type": "gpu_1x_a6000",
                "region": "us-west-1", 
                "ssh_key_name": "orchestra-deployment-key",
                "ssh_public_key": self.ssh_public_key
            }
        )
        instances["vector_db"] = vector_db
        
        return instances
    
    def setup_instance_software(self, instance: LambdaLabsInstance, setup_type: str) -> command.remote.Command:
        """Setup software on Lambda Labs instance"""
        
        setup_scripts = {
            "api_server": self._get_api_server_setup_script(),
            "mcp_server": self._get_mcp_server_setup_script(),
            "vector_db": self._get_vector_db_setup_script()
        }
        
        setup_command = command.remote.Command(
            f"setup-{setup_type}",
            connection=command.remote.ConnectionArgs(
                host=instance.ip,
                user="ubuntu",
                private_key=self.ssh_private_key
            ),
            create=setup_scripts[setup_type],
            opts=pulumi.ResourceOptions(
                depends_on=[instance]
            )
        )
        
        return setup_command
    
    def _get_api_server_setup_script(self) -> str:
        """Get setup script for API server"""
        return f"""#!/bin/bash
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker and NVIDIA Container Toolkit
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install NVIDIA drivers and CUDA
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

# Clone Orchestra AI
cd /opt
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
cat > .env << 'EOF'
LAMBDA_API_KEY={secret_manager.get_secret("LAMBDA_API_KEY", "")}
GITHUB_TOKEN={secret_manager.get_secret("GITHUB_TOKEN", "")}
VERCEL_TOKEN={secret_manager.get_secret("VERCEL_TOKEN", "")}
OPENAI_API_KEY={secret_manager.get_secret("OPENAI_API_KEY", "")}
PORTKEY_API_KEY={secret_manager.get_secret("PORTKEY_API_KEY", "")}
DATABASE_URL={secret_manager.get_secret("DATABASE_URL", "")}
REDIS_URL={secret_manager.get_secret("REDIS_URL", "")}
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Create systemd service
cat > /etc/systemd/system/orchestra-api.service << 'EOF'
[Unit]
Description=Orchestra AI API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/orchestra-main
Environment=PATH=/opt/orchestra-main/venv/bin
EnvironmentFile=/opt/orchestra-main/.env
ExecStart=/opt/orchestra-main/venv/bin/python api/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable orchestra-api
systemctl start orchestra-api

echo "✅ Orchestra AI API Server setup complete!"
"""
    
    def _get_mcp_server_setup_script(self) -> str:
        """Get setup script for MCP server"""
        return """#!/bin/bash
set -e

# Update system and install dependencies
apt-get update && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git

# Clone Orchestra AI
cd /opt
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create MCP service
cat > /etc/systemd/system/orchestra-mcp.service << 'EOF'
[Unit]
Description=Orchestra AI MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/orchestra-main
Environment=PATH=/opt/orchestra-main/venv/bin
ExecStart=/opt/orchestra-main/venv/bin/python mcp_unified_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable orchestra-mcp
systemctl start orchestra-mcp

echo "✅ Orchestra AI MCP Server setup complete!"
"""
    
    def _get_vector_db_setup_script(self) -> str:
        """Get setup script for vector database"""
        return """#!/bin/bash
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install NVIDIA drivers for GPU acceleration
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update
apt-get -y install cuda-toolkit-12-3

# Setup Weaviate with GPU support
mkdir -p /opt/weaviate
cd /opt/weaviate

cat > docker-compose.yml << 'EOF'
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
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'orchestra-api-key'
      AUTHENTICATION_APIKEY_USERS: 'orchestra@admin'
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

echo "✅ Vector Database setup complete!"
"""

# Initialize and export if running directly
if __name__ == "__main__":
    # Create Lambda Labs infrastructure
    lambda_infra = LambdaLabsInfrastructure()
    
    # Create cluster
    instances = lambda_infra.create_orchestra_cluster()
    
    # Setup software on each instance
    setup_commands = {}
    for instance_type, instance in instances.items():
        setup_commands[instance_type] = lambda_infra.setup_instance_software(instance, instance_type)
    
    # Export instance information
    for instance_type, instance in instances.items():
        pulumi.export(f"{instance_type}_id", instance.id)
        pulumi.export(f"{instance_type}_ip", instance.ip)
        pulumi.export(f"{instance_type}_status", instance.status)
    
    # Export cluster information
    pulumi.export("cluster_size", len(instances))
    pulumi.export("cluster_regions", ["us-east-1", "us-west-1"])
    pulumi.export("infrastructure_type", "lambda_labs_gpu_cluster")

