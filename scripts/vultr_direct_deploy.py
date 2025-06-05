import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Direct Vultr deployment using Vultr API
Deploys cherry_ai MCP infrastructure without Pulumi
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import paramiko
import base64

class VultrDirectDeployment:
    def __init__(self):
        self.api_key = os.getenv("VULTR_API_KEY")
        if not self.api_key:
            print("❌ VULTR_API_KEY not found in environment")
            print("   Please add it to your .env file")
            sys.exit(1)
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.vultr.com/v2"
        self.ssh_key_path = Path.home() / ".ssh/cherry_ai_deploy"
        self.instances = []
        
    def run(self):
        """Execute deployment"""
        print("🚀 Starting Direct Vultr Deployment")
        print("=" * 50)
        
        try:
            # Create SSH key
            ssh_key_id = self.create_ssh_key()
            
            # Create firewall group
            firewall_id = self.create_firewall_group()
            
            # Create VPC
            vpc_id = self.create_vpc()
            
            # Create instances
            db_instance = self.create_instance(
                label="cherry_ai-db",
                plan="vc2-4c-8gb",  # 4 vCPU, 8GB RAM
                ssh_key_id=ssh_key_id,
                firewall_id=firewall_id,
                vpc_id=vpc_id,
                user_data=self.get_user_data("database")
            )
            
            app_instances = []
            for i in range(2):  # Create 2 app servers
                app_instance = self.create_instance(
                    label=f"cherry_ai-app-{i}",
                    plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
                    ssh_key_id=ssh_key_id,
                    firewall_id=firewall_id,
                    vpc_id=vpc_id,
                    user_data=self.get_user_data("application")
                )
                app_instances.append(app_instance)
                
            # Create load balancer
            lb_id = self.create_load_balancer(app_instances)
            
            # Wait for instances to be ready
            print("\n⏳ Waiting for instances to be ready...")
            self.wait_for_instances([db_instance] + app_instances)
            
            # Get instance details
            instances_info = self.get_instances_info([db_instance] + app_instances)
            lb_info = self.get_load_balancer_info(lb_id)
            
            # Save deployment info
            self.save_deployment_info(instances_info, lb_info, vpc_id, firewall_id)
            
            # Configure and deploy
            self.configure_and_deploy(instances_info)
            
            print("\n✅ Deployment complete!")
            self.print_access_info(lb_info)
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            self.cleanup()
            sys.exit(1)
            
    def create_ssh_key(self):
        """Create or get SSH key"""
        print("\n🔑 Setting up SSH key...")
        
        # Read public key
        pub_key_path = Path(str(self.ssh_key_path) + ".pub")
        if not pub_key_path.exists():
            print("   Generating SSH key...")
            subprocess.run([
                "ssh-keygen", "-t", "rsa", "-b", "4096",
                "-f", str(self.ssh_key_path),
                "-N", "", "-C", "cherry_ai-deploy"
            ], check=True)
            
        ssh_key_content = pub_key_path.read_text().strip()
        
        # Check if key already exists
        response = requests.get(f"{self.base_url}/ssh-keys", headers=self.headers)
        if response.status_code == 200:
            for key in response.json()["ssh_keys"]:
                if key["name"] == "cherry_ai-deploy":
                    print(f"   ✓ Using existing SSH key: {key['id']}")
                    return key["id"]
                    
        # Create new key
        data = {
            "name": "cherry_ai-deploy",
            "ssh_key": ssh_key_content
        }
        response = requests.post(f"{self.base_url}/ssh-keys", headers=self.headers, json=data)
        if response.status_code == 201:
            key_id = response.json()["ssh_key"]["id"]
            print(f"   ✓ Created SSH key: {key_id}")
            return key_id
        else:
            raise Exception(f"Failed to create SSH key: {response.text}")
            
    def create_firewall_group(self):
        """Create firewall group with rules"""
        print("\n🔥 Creating firewall group...")
        
        # Create group
        data = {"description": "cherry_ai MCP Firewall"}
        response = requests.post(f"{self.base_url}/firewalls", headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception(f"Failed to create firewall group: {response.text}")
            
        firewall_id = response.json()["firewall_group"]["id"]
        print(f"   ✓ Created firewall group: {firewall_id}")
        
        # Add rules
        rules = [
            {"protocol": "tcp", "port": "22", "subnet": "0.0.0.0", "subnet_size": 0, "notes": "SSH"},
            {"protocol": "tcp", "port": "80", "subnet": "0.0.0.0", "subnet_size": 0, "notes": "HTTP"},
            {"protocol": "tcp", "port": "443", "subnet": "0.0.0.0", "subnet_size": 0, "notes": "HTTPS"},
            {"protocol": "tcp", "port": "8000", "subnet": "0.0.0.0", "subnet_size": 0, "notes": "API"},
            {"protocol": "tcp", "port": "3000", "subnet": "0.0.0.0", "subnet_size": 0, "notes": "Grafana"},
            {"protocol": "tcp", "port": "5432", "subnet": "10.0.0.0", "subnet_size": 24, "notes": "PostgreSQL"},
            {"protocol": "tcp", "port": "6379", "subnet": "10.0.0.0", "subnet_size": 24, "notes": "Redis"},
            {"protocol": "tcp", "port": "8080", "subnet": "10.0.0.0", "subnet_size": 24, "notes": "Weaviate"},
        ]
        
        for rule in rules:
            rule["type"] = "v4"
            response = requests.post(
                f"{self.base_url}/firewalls/{firewall_id}/rules",
                headers=self.headers,
                json=rule
            )
            if response.status_code == 204:
                print(f"   ✓ Added rule: {rule['notes']}")
                
        return firewall_id
        
    def create_vpc(self):
        """Create VPC network"""
        print("\n🌐 Creating VPC...")
        
        data = {
            "region": "ewr",  # New Jersey
            "description": "cherry_ai MCP VPC",
            "v4_subnet": "10.0.0.0",
            "v4_subnet_mask": 24
        }
        
        response = requests.post(f"{self.base_url}/vpcs", headers=self.headers, json=data)
        if response.status_code == 201:
            vpc_id = response.json()["vpc"]["id"]
            print(f"   ✓ Created VPC: {vpc_id}")
            return vpc_id
        else:
            raise Exception(f"Failed to create VPC: {response.text}")
            
    def get_user_data(self, role: str) -> str:
        """Get user data script for instance initialization"""
        base_script = """#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install monitoring tools
apt-get install -y htop iotop nethogs git

# Setup swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Configure sysctl for performance
cat >> /etc/sysctl.conf <<EOF
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
EOF
sysctl -p

# Create app directory
mkdir -p /opt/cherry_ai
cd /opt/cherry_ai

# Set role
echo 'SERVER_ROLE={role}' > /opt/cherry_ai/.role
""".format(role=role)
        
        return base64.b64encode(base_script.encode()).decode()
        
    def create_instance(self, label: str, plan: str, ssh_key_id: str, 
                       firewall_id: str, vpc_id: str, user_data: str) -> str:
        """Create a Vultr instance"""
        print(f"\n🖥️  Creating instance: {label}...")
        
        data = {
            "region": "ewr",
            "plan": plan,
            "os_id": 1743,  # Ubuntu 22.04 LTS
            "label": label,
            "hostname": label,
            "enable_ipv6": True,
            "backups": "enabled",
            "ddos_protection": True,
            "sshkey_id": [ssh_key_id],
            "firewall_group_id": firewall_id,
            "vpc_ids": [vpc_id],
            "user_data": user_data,
            "tags": ["cherry_ai", "production"]
        }
        
        response = requests.post(f"{self.base_url}/instances", headers=self.headers, json=data)
        if response.status_code == 202:
            instance_id = response.json()["instance"]["id"]
            self.instances.append(instance_id)
            print(f"   ✓ Created instance: {instance_id}")
            return instance_id
        else:
            raise Exception(f"Failed to create instance: {response.text}")
            
    def create_load_balancer(self, app_instances: List[str]) -> str:
        """Create load balancer"""
        print("\n⚖️  Creating load balancer...")
        
        data = {
            "region": "ewr",
            "label": "cherry_ai-lb",
            "balancing_algorithm": "roundrobin",
            "proxy_protocol": False,
            "ssl_redirect": True,
            "http2": True,
            "forwarding_rules": [
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
                    "backend_protocol": "http",
                    "backend_port": 8000
                },
                {
                    "frontend_protocol": "https",
                    "frontend_port": 443,
                    "backend_protocol": "http",
                    "backend_port": 8000
                }
            ],
            "health_check": {
                "protocol": "http",
                "port": 8000,
                "path": "/health",
                "check_interval": 10,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            "instances": app_instances
        }
        
        response = requests.post(f"{self.base_url}/load-balancers", headers=self.headers, json=data)
        if response.status_code == 202:
            lb_id = response.json()["load_balancer"]["id"]
            print(f"   ✓ Created load balancer: {lb_id}")
            return lb_id
        else:
            raise Exception(f"Failed to create load balancer: {response.text}")
            
    def wait_for_instances(self, instance_ids: List[str]):
        """Wait for instances to be active"""
        for instance_id in instance_ids:
            print(f"   Waiting for {instance_id}...", end="", flush=True)
            
            max_attempts = 60
            for i in range(max_attempts):
                response = requests.get(
                    f"{self.base_url}/instances/{instance_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    status = response.json()["instance"]["status"]
                    if status == "active":
                        print(" ✓")
                        break
                        
                if i == max_attempts - 1:
                    print(" ❌")
                    raise Exception(f"Instance {instance_id} failed to become active")
                    
                # TODO: Replace with asyncio.sleep() for async code
                time.sleep(5)
                print(".", end="", flush=True)
                
    def get_instances_info(self, instance_ids: List[str]) -> List[Dict]:
        """Get instance information"""
        instances_info = []
        
        for instance_id in instance_ids:
            response = requests.get(
                f"{self.base_url}/instances/{instance_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                instance = response.json()["instance"]
                instances_info.append({
                    "id": instance_id,
                    "label": instance["label"],
                    "main_ip": instance["main_ip"],
                    "internal_ip": instance["internal_ip"],
                    "plan": instance["plan"],
                    "status": instance["status"]
                })
                
        return instances_info
        
    def get_load_balancer_info(self, lb_id: str) -> Dict:
        """Get load balancer information"""
        response = requests.get(
            f"{self.base_url}/load-balancers/{lb_id}",
            headers=self.headers
        )
        if response.status_code == 200:
            lb = response.json()["load_balancer"]
            return {
                "id": lb_id,
                "ipv4": lb["ipv4"],
                "ipv6": lb["ipv6"],
                "status": lb["status"]
            }
        else:
            raise Exception(f"Failed to get load balancer info: {response.text}")
            
    def save_deployment_info(self, instances: List[Dict], lb: Dict, vpc_id: str, firewall_id: str):
        """Save deployment information"""
        deployment_info = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "vpc_id": vpc_id,
            "firewall_id": firewall_id,
            "load_balancer": lb,
            "instances": instances
        }
        
        with open("deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
            
        print("\n📄 Saved deployment info to deployment_info.json")
        
    def configure_and_deploy(self, instances: List[Dict]):
        """Configure instances and deploy application"""
        print("\n🚀 Configuring and deploying application...")
        
        # Find database instance
        db_instance = next(i for i in instances if "db" in i["label"])
        app_instances = [i for i in instances if "app" in i["label"]]
        
        # Configure database first
        print(f"\n   Configuring database ({db_instance['main_ip']})...")
        self.configure_instance(db_instance, "database", db_instance["internal_ip"])
        
        # Configure app instances
        for app in app_instances:
            print(f"\n   Configuring {app['label']} ({app['main_ip']})...")
            self.configure_instance(app, "application", db_instance["internal_ip"])
            
    def configure_instance(self, instance: Dict, role: str, db_ip: str):
        """Configure individual instance"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Wait for SSH to be ready
        max_attempts = 30
        for i in range(max_attempts):
            try:
                ssh.connect(
                    instance["main_ip"],
                    username="root",
                    key_filename=str(self.ssh_key_path),
                    timeout=10
                )
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if i == max_attempts - 1:
                    # TODO: Replace with asyncio.sleep() for async code
                    raise Exception(f"Failed to connect to {instance['label']}")
                time.sleep(10)
                
        try:
            # Clone repository
            print("     - Cloning repository...")
            ssh.exec_command("cd /opt && git clone https://github.com/yourusername/conductor-mcp.git cherry_ai")
            
            # Copy environment file
            print("     - Setting up environment...")
            sftp = ssh.open_sftp()
            sftp.put(".env", "/opt/cherry_ai/.env")
            
            # Update environment for role
            if role == "database":
                ssh.exec_command("echo 'POSTGRES_HOST=0.0.0.0' >> /opt/cherry_ai/.env")
            else:
                ssh.exec_command(f"echo 'POSTGRES_HOST={db_ip}' >> /opt/cherry_ai/.env")
                ssh.exec_command(f"echo 'REDIS_URL=redis://{db_ip}:6379/0' >> /opt/cherry_ai/.env")
                ssh.exec_command(f"echo 'WEAVIATE_URL=http://{db_ip}:8080' >> /opt/cherry_ai/.env")
                
            # Start services
            print("     - Starting services...")
            if role == "database":
                commands = [
                    "cd /opt/cherry_ai",
                    "docker-compose up -d postgres redis weaviate",
                    "sleep 30",
                    "docker-compose exec -T postgres psql -U postgres -c 'CREATE DATABASE cherry_ai;' || true"
                ]
            else:
                commands = [
                    "cd /opt/cherry_ai",
                    "docker-compose up -d api admin-ui nginx"
                ]
                
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                stdout.read()
                
            print("     ✓ Configuration complete")
            
        finally:
            ssh.close()
            
    def print_access_info(self, lb_info: Dict):
        """Print access information"""
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        
        print(f"\n📍 Access Points:")
        print(f"   API: http://{lb_info['ipv4']}:8000")
        print(f"   Admin UI: http://{lb_info['ipv4']}:8000/admin")
        print(f"   Grafana: http://{lb_info['ipv4']}:3000")
        
        print(f"\n🔑 Credentials:")
        print(f"   API Key: {os.getenv('API_KEY', 'Check .env file')}")
        
        print(f"\n📝 Next Steps:")
        print(f"   1. Update DNS to point to {lb_info['ipv4']}")
        print(f"   2. Configure SSL certificate")
        print(f"   3. Set up monitoring alerts")
        
    def cleanup(self):
        """Cleanup resources on failure"""
        print("\n🧹 Cleaning up resources...")
        
        for instance_id in self.instances:
            try:
                requests.delete(
                    f"{self.base_url}/instances/{instance_id}",
                    headers=self.headers
                )
                print(f"   ✓ Deleted instance: {instance_id}")
            except:
                pass

if __name__ == "__main__":
    deployment = VultrDirectDeployment()
    deployment.run()