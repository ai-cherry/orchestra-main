#!/usr/bin/env python3
"""
Lambda Labs Infrastructure using Pulumi
Provisions and manages Lambda Labs GPU instances for Orchestra
"""

import pulumi
import pulumi_command as command
import json
import time
from typing import Dict, Optional

# Configuration
config = pulumi.Config()
lambda_api_key = config.require_secret("lambda:api_key")
ssh_key_id = config.require_int("lambda:ssh_key_id")
instance_type = config.get("lambda:instance_type") or "gpu_1x_a10"
region = config.get("lambda:region") or "us-west-1"
instance_name = config.get("lambda:instance_name") or "orchestra-dev"

class LambdaLabsInstance(pulumi.ComponentResource):
    """
    Custom Pulumi component for Lambda Labs instance management
    """
    
    def __init__(self, name: str, args: Dict, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__("lambda:Instance", name, None, opts)
        
        self.name = name
        self.instance_type = args.get("instance_type", "gpu_1x_a10")
        self.region = args.get("region", "us-west-1")
        self.ssh_key_ids = args.get("ssh_key_ids", [])
        
        # Create instance via Lambda Labs API
        self.create_instance = command.local.Command(
            f"{name}-create",
            create=lambda_api_key.apply(lambda key: self._create_command(key)),
            delete=lambda_api_key.apply(lambda key: self._delete_command(key)),
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Parse the response to get instance details
        self.instance_data = self.create_instance.stdout.apply(self._parse_instance_response)
        self.instance_id = self.instance_data.apply(lambda data: data.get("id", ""))
        self.ip_address = self.instance_data.apply(lambda data: data.get("ip", ""))
        
        # Wait for instance to be ready
        self.wait_ready = command.local.Command(
            f"{name}-wait-ready",
            create=pulumi.Output.all(lambda_api_key, self.instance_id).apply(
                lambda args: self._wait_ready_command(args[0], args[1])
            ),
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.create_instance])
        )
        
        # Configure instance
        self.configure = command.remote.Command(
            f"{name}-configure",
            connection=command.remote.ConnectionArgs(
                host=self.ip_address,
                user="ubuntu",
                private_key=config.get("ssh_private_key") or "~/.ssh/id_rsa"
            ),
            create="""
                sudo apt-get update &&
                sudo apt-get install -y python3-pip python3-venv git docker.io docker-compose &&
                sudo usermod -aG docker ubuntu &&
                echo 'Instance configured successfully'
            """,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.wait_ready])
        )
        
        self.register_outputs({
            "instance_id": self.instance_id,
            "ip_address": self.ip_address,
            "instance_type": self.instance_type,
            "region": self.region
        })
    
    def _create_command(self, api_key: str) -> str:
        """Generate the create instance command"""
        data = {
            "instance_type": self.instance_type,
            "region": self.region,
            "ssh_key_ids": self.ssh_key_ids,
            "quantity": 1,
            "name": self.name
        }
        
        return f"""
        curl -s -X POST \
          -H "Authorization: Bearer {api_key}" \
          -H "Content-Type: application/json" \
          -d '{json.dumps(data)}' \
          https://cloud.lambdalabs.com/api/v1/instances
        """
    
    def _delete_command(self, api_key: str) -> str:
        """Generate the delete instance command"""
        return f"""
        # Get instance ID by name
        INSTANCE_ID=$(curl -s -H "Authorization: Bearer {api_key}" \
          https://cloud.lambdalabs.com/api/v1/instances | \
          jq -r '.data[] | select(.name == "{self.name}") | .id')
        
        # Terminate instance if found
        if [ ! -z "$INSTANCE_ID" ]; then
          curl -s -X POST \
            -H "Authorization: Bearer {api_key}" \
            -H "Content-Type: application/json" \
            -d '{{"instance_ids": ["'$INSTANCE_ID'"]}}' \
            https://cloud.lambdalabs.com/api/v1/instances/terminate
        fi
        """
    
    def _parse_instance_response(self, response: str) -> Dict:
        """Parse the API response to extract instance details"""
        try:
            data = json.loads(response)
            if "data" in data and "instances" in data["data"]:
                instances = data["data"]["instances"]
                if instances:
                    return instances[0]
            return {}
        except:
            return {}
    
    def _wait_ready_command(self, api_key: str, instance_id: str) -> str:
        """Generate command to wait for instance to be ready"""
        return f"""
        for i in {{1..30}}; do
          STATUS=$(curl -s -H "Authorization: Bearer {api_key}" \
            https://cloud.lambdalabs.com/api/v1/instances/{instance_id} | \
            jq -r '.data.status')
          
          if [ "$STATUS" = "active" ]; then
            echo "Instance is active"
            exit 0
          fi
          
          echo "Waiting for instance... (attempt $i/30, status: $STATUS)"
          sleep 10
        done
        
        echo "Instance did not become active in time"
        exit 1
        """

# Create the Lambda Labs instance
instance = LambdaLabsInstance(
    instance_name,
    {
        "instance_type": instance_type,
        "region": region,
        "ssh_key_ids": [ssh_key_id]
    }
)

# Set up Orchestra environment on the instance
setup_orchestra = command.remote.Command(
    "setup-orchestra",
    connection=command.remote.ConnectionArgs(
        host=instance.ip_address,
        user="ubuntu",
        private_key=config.get("ssh_private_key") or "~/.ssh/id_rsa"
    ),
    create=f"""
        # Clone the repository
        if [ ! -d ~/orchestra-main ]; then
            git clone https://github.com/lynnmusil/orchestra-main.git ~/orchestra-main
        fi
        
        cd ~/orchestra-main
        
        # Set up Python environment
        python3 -m venv venv
        source venv/bin/activate
        
        # Install dependencies
        if [ -f requirements.txt ]; then
            pip install -r requirements.txt
        fi
        
        # Set up environment variables
        cat > .env << EOF
LAMBDA_API_KEY={config.get("lambda:api_key") or ""}
GITHUB_TOKEN={config.get("github:token") or ""}
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
EOF
        
        # Run setup script if it exists
        if [ -f setup_mcp_environment.sh ]; then
            chmod +x setup_mcp_environment.sh
            ./setup_mcp_environment.sh
        fi
        
        echo "Orchestra environment setup complete"
    """,
    opts=pulumi.ResourceOptions(depends_on=[instance.configure])
)

# Create systemd services for MCP servers
mcp_services = command.remote.Command(
    "mcp-services",
    connection=command.remote.ConnectionArgs(
        host=instance.ip_address,
        user="ubuntu",
        private_key=config.get("ssh_private_key") or "~/.ssh/id_rsa"
    ),
    create="""
        # Create systemd service for MCP server
        sudo tee /etc/systemd/system/mcp-server.service > /dev/null << 'EOF'
[Unit]
Description=MCP Server for Orchestra
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/orchestra-main
Environment="PATH=/home/ubuntu/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/orchestra-main/venv/bin/python /home/ubuntu/orchestra-main/mcp_server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        # Enable and start the service
        sudo systemctl daemon-reload
        sudo systemctl enable mcp-server
        sudo systemctl start mcp-server
        
        echo "MCP services configured"
    """,
    opts=pulumi.ResourceOptions(depends_on=[setup_orchestra])
)

# Export outputs
pulumi.export("instance_id", instance.instance_id)
pulumi.export("ip_address", instance.ip_address)
pulumi.export("instance_type", instance.instance_type)
pulumi.export("region", instance.region)
pulumi.export("ssh_command", instance.ip_address.apply(lambda ip: f"ssh ubuntu@{ip}"))
pulumi.export("vscode_command", instance.ip_address.apply(
    lambda ip: f"code --remote ssh-remote+ubuntu@{ip} /home/ubuntu/orchestra-main"
))