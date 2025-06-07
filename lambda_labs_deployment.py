#!/usr/bin/env python3
"""
Lambda Labs Deployment with Pulumi
AI Orchestration Infrastructure
"""

import pulumi
import pulumi_command as command
from pulumi import Config, Output, export
import json
import os

# Configuration
config = Config()
project_name = "ai-orchestration"
environment = config.get("environment") or "production"

# Lambda Labs Configuration
lambda_config = {
    "api_key": os.getenv("LAMBDA_API_KEY"),
    "ssh_key": os.getenv("LAMBDA_SSH_KEY"),
    "instance_type": config.get("instance_type") or "gpu_1x_a10",
    "region": config.get("region") or "us-west-1",
    "os": "ubuntu-22.04"
}

# Database Configuration from environment
db_config = {
    "postgresql_url": os.getenv("DATABASE_URL"),
    "redis_url": os.getenv("REDIS_URL"),
    "weaviate_url": os.getenv("WEAVIATE_URL"),
    "pinecone_api_key": os.getenv("PINECONE_API_KEY")
}

class LambdaLabsInstance:
    """Lambda Labs GPU Instance for AI Orchestration"""
    
    def __init__(self, name: str):
        self.name = name
        
        # Create Lambda Labs instance using API
        self.create_instance_cmd = command.local.Command(
            f"{name}-create",
            create=f"""
            curl -X POST https://cloud.lambdalabs.com/api/v1/instances \\
                -H "Authorization: Bearer {lambda_config['api_key']}" \\
                -H "Content-Type: application/json" \\
                -d '{json.dumps({
                    "name": "{name}-{environment}",
                    "instance_type": "{lambda_config['instance_type']}",
                    "region": "{lambda_config['region']}",
                    "ssh_key_names": ["orchestra-key"],
                    "file_system_names": [],
                    "quantity": 1
                })}'
            """,
            opts=pulumi.ResourceOptions(
                custom_timeouts=pulumi.CustomTimeouts(create="10m")
            )
        )
        
        # Extract instance details
        self.instance_id = Output.json_parse(
            self.create_instance_cmd.stdout
        ).apply(lambda x: x.get("data", {}).get("instance_ids", [None])[0])
        
        self.instance_ip = Output.json_parse(
            self.create_instance_cmd.stdout
        ).apply(lambda x: x.get("data", {}).get("instances", [{}])[0].get("ip"))

class AIOrchestrationStack:
    """Complete AI Orchestration Stack on Lambda Labs"""
    
    def __init__(self):
        # Create main compute instance
        self.main_instance = LambdaLabsInstance("orchestra-main")
        
        # Setup script for the instance
        self.setup_script = """#!/bin/bash
set -e

echo "🚀 Setting up AI Orchestration on Lambda Labs"

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL client
sudo apt-get install -y postgresql-client

# Install Redis tools
sudo apt-get install -y redis-tools

# Clone repository
git clone https://github.com/yourusername/orchestra-main-3.git /home/ubuntu/orchestra
cd /home/ubuntu/orchestra

# Create .env file
cat > .env << 'EOF'
{env_content}
EOF

# Install Python dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements_ai_orchestration.txt

# Create systemd service
sudo tee /etc/systemd/system/ai-orchestration.service > /dev/null << 'EOF'
[Unit]
Description=AI Orchestration Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/orchestra
Environment="PATH=/home/ubuntu/orchestra/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/orchestra/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-orchestration
sudo systemctl start ai-orchestration

# Setup monitoring
docker run -d \\
    --name prometheus \\
    -p 9090:9090 \\
    -v /home/ubuntu/orchestra/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \\
    prom/prometheus

# Setup Grafana
docker run -d \\
    --name grafana \\
    -p 3000:3000 \\
    grafana/grafana

echo "✅ AI Orchestration setup complete!"
"""
        
        # Configure the instance
        self.configure_cmd = command.remote.Command(
            "configure-instance",
            connection=command.remote.ConnectionArgs(
                host=self.main_instance.instance_ip,
                user="ubuntu",
                private_key=lambda_config["ssh_key"]
            ),
            create=self.setup_script.format(
                env_content=self._get_env_content()
            ),
            opts=pulumi.ResourceOptions(
                depends_on=[self.main_instance.create_instance_cmd]
            )
        )
        
        # Export outputs
        export("instance_id", self.main_instance.instance_id)
        export("instance_ip", self.main_instance.instance_ip)
        export("api_endpoint", Output.concat("http://", self.main_instance.instance_ip, ":8000"))
        export("monitoring_endpoint", Output.concat("http://", self.main_instance.instance_ip, ":3000"))
        
    def _get_env_content(self) -> str:
        """Get environment content for deployment"""
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                return f.read()
        return ""

# Create Pulumi program
def pulumi_program():
    """Main Pulumi program"""
    stack = AIOrchestrationStack()
    
    # Additional resources can be added here
    # For example: backup volumes, monitoring alerts, etc.
    
    return {
        "instance_id": stack.main_instance.instance_id,
        "instance_ip": stack.main_instance.instance_ip,
        "api_endpoint": Output.concat("http://", stack.main_instance.instance_ip, ":8000"),
        "monitoring_endpoint": Output.concat("http://", stack.main_instance.instance_ip, ":3000")
    }

# Helper script for deployment
if __name__ == "__main__":
    import subprocess
    import sys
    
    print("🚀 Lambda Labs Deployment Helper")
    print("================================")
    
    # Check for required environment variables
    required_vars = ["LAMBDA_API_KEY", "DATABASE_URL", "REDIS_URL", "WEAVIATE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease ensure .env file is properly configured")
        sys.exit(1)
    
    print("✅ Environment variables configured")
    
    # Deployment options
    print("\nDeployment Options:")
    print("1. Deploy new stack")
    print("2. Update existing stack")
    print("3. Destroy stack")
    print("4. Show stack outputs")
    
    choice = input("\nSelect option (1-4): ")
    
    if choice == "1":
        print("\n🔨 Creating new stack...")
        subprocess.run(["pulumi", "up", "--yes"])
    elif choice == "2":
        print("\n🔄 Updating stack...")
        subprocess.run(["pulumi", "up", "--yes"])
    elif choice == "3":
        print("\n🗑️  Destroying stack...")
        subprocess.run(["pulumi", "destroy", "--yes"])
    elif choice == "4":
        print("\n📊 Stack outputs:")
        subprocess.run(["pulumi", "stack", "output"])
    else:
        print("❌ Invalid option")