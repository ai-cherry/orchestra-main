import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Deploy cherry_ai MCP to Vultr
Automated deployment script with health checks
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List
import paramiko
import requests

class VultrDeployment:
    def __init__(self):
        self.base_dir = Path("/root/cherry_ai-main")
        self.deployment_info = None
        self.ssh_key_path = os.getenv("SSH_PRIVATE_KEY_PATH", "~/.ssh/id_rsa")
        
    def run(self):
        """Execute deployment process"""
        print("🚀 Starting cherry_ai MCP Deployment to Vultr")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        # Deploy infrastructure
        if not self.deploy_infrastructure():
            return False
            
        # Wait for servers to be ready
        if not self.wait_for_servers():
            return False
            
        # Configure servers
        if not self.configure_servers():
            return False
            
        # Deploy application
        if not self.deploy_application():
            return False
            
        # Run health checks
        if not self.health_check():
            return False
            
        print("\n✅ Deployment completed successfully!")
        self.print_access_info()
        return True
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("\n🔍 Checking prerequisites...")
        
        # Check for required environment variables
        required_vars = [
            "VULTR_API_KEY",
            "POSTGRES_PASSWORD",
            "API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("   Please set these in your .env file")
            return False
            
        # Check for Pulumi
        try:
            subprocess.run(["pulumi", "version"], check=True, capture_output=True)
            print("  ✓ Pulumi installed")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print("❌ Pulumi not installed. Install with: curl -fsSL https://get.pulumi.com | sh")
            return False
            
        # Check for SSH key
        ssh_key = Path(self.ssh_key_path).expanduser()
        if not ssh_key.exists():
            print(f"❌ SSH private key not found at {self.ssh_key_path}")
            return False
            
        print("  ✓ All prerequisites met")
        return True
        
    def deploy_infrastructure(self):
        """Deploy infrastructure using Pulumi"""
        print("\n🏗️  Deploying infrastructure...")
        
        os.chdir(self.base_dir / "infrastructure")
        
        # Initialize Pulumi stack
        try:
            subprocess.run(["pulumi", "stack", "init", "production"], capture_output=True)
        except:
            # Stack might already exist
            subprocess.run(["pulumi", "stack", "select", "production"], check=True)
            
        # Set configuration
        config_values = {
            "vultr:apiKey": os.getenv("VULTR_API_KEY"),
            "ssh_public_key": self.get_ssh_public_key(),
            "environment": "production",
            "region": os.getenv("VULTR_REGION", "ewr"),
            "app_server_count": "2"
        }
        
        for key, value in config_values.items():
            subprocess.run(["pulumi", "config", "set", key, value], check=True)
            
        # Deploy
        print("  ⏳ Running Pulumi deployment (this may take 5-10 minutes)...")
        result = subprocess.run(["pulumi", "up", "-y"], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Deployment failed: {result.stderr}")
            return False
            
        # Get outputs
        outputs = {}
        output_keys = ["vpc_id", "load_balancer_ip", "db_server_private_ip", "app_server_private_ips"]
        
        for key in output_keys:
            result = subprocess.run(["pulumi", "stack", "output", key], capture_output=True, text=True)
            outputs[key] = result.stdout.strip()
            
        # Load deployment info
        deployment_file = self.base_dir / "infrastructure/deployment-production.json"
        if deployment_file.exists():
            with open(deployment_file, 'r') as f:
                self.deployment_info = json.load(f)
                
        print("  ✓ Infrastructure deployed successfully")
        return True
        
    def get_ssh_public_key(self):
        """Get SSH public key"""
        pub_key_path = Path(self.ssh_key_path + ".pub").expanduser()
        if pub_key_path.exists():
            return pub_key_path.read_text().strip()
        else:
            # Generate from private key
            result = subprocess.run(
                ["ssh-keygen", "-y", "-f", Path(self.ssh_key_path).expanduser()],
                capture_output=True, text=True
            )
            return result.stdout.strip()
            
    def wait_for_servers(self):
        """Wait for servers to be ready"""
        print("\n⏳ Waiting for servers to be ready...")
        
        if not self.deployment_info:
            print("❌ No deployment info found")
            return False
            
        # Get server IPs
        servers = [self.deployment_info["database"]] + self.deployment_info["app_servers"]
        
        for server in servers:
            ip = server["public_ip"]
            print(f"  Waiting for {ip}...", end="", flush=True)
            
            # Wait for SSH to be ready
            max_attempts = 30
            for i in range(max_attempts):
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        ip,
                        username="root",
                        key_filename=str(Path(self.ssh_key_path).expanduser()),
                        timeout=5
                    )
                    ssh.close()
                    print(" ✓")
                    break
                except:
                    if i == max_attempts - 1:
                        print(" ❌")
                        return False
                    # TODO: Replace with asyncio.sleep() for async code
                    time.sleep(10)
                    print(".", end="", flush=True)
                    
        print("  ✓ All servers ready")
        return True
        
    def configure_servers(self):
        """Configure servers with Docker and dependencies"""
        print("\n🔧 Configuring servers...")
        
        # Configure database server
        db_server = self.deployment_info["database"]
        if not self.configure_server(db_server["public_ip"], "database"):
            return False
            
        # Configure app servers
        for i, server in enumerate(self.deployment_info["app_servers"]):
            if not self.configure_server(server["public_ip"], f"app-{i}"):
                return False
                
        print("  ✓ All servers configured")
        return True
        
    def configure_server(self, ip: str, role: str):
        """Configure individual server"""
        print(f"  Configuring {role} server ({ip})...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            ip,
            username="root",
            key_filename=str(Path(self.ssh_key_path).expanduser())
        )
        
        try:
            # Copy application files
            sftp = ssh.open_sftp()
            
            # Create directories
            ssh.exec_command("mkdir -p /opt/cherry_ai/scripts")
            ssh.exec_command("mkdir -p /opt/cherry_ai/mcp_server")
            ssh.exec_command("mkdir -p /opt/cherry_ai/infrastructure")
            
            # Copy essential files
            files_to_copy = [
                ("docker-compose.yml", "/opt/cherry_ai/docker-compose.yml"),
                (".env", "/opt/cherry_ai/.env"),
                ("scripts/start_cherry_ai_services.py", "/opt/cherry_ai/scripts/start_cherry_ai_services.py"),
            ]
            
            for local, remote in files_to_copy:
                local_path = self.base_dir / local
                if local_path.exists():
                    sftp.put(str(local_path), remote)
                    
            # Copy directories
            self._copy_directory(sftp, ssh, self.base_dir / "mcp_server", "/opt/cherry_ai/mcp_server")
            
            # Update .env with server-specific settings
            if role == "database":
                ssh.exec_command(f"echo 'SERVER_ROLE=database' >> /opt/cherry_ai/.env")
                ssh.exec_command(f"echo 'POSTGRES_HOST=0.0.0.0' >> /opt/cherry_ai/.env")
            else:
                db_ip = self.deployment_info["database"]["private_ip"]
                ssh.exec_command(f"echo 'SERVER_ROLE=application' >> /opt/cherry_ai/.env")
                ssh.exec_command(f"echo 'POSTGRES_HOST={db_ip}' >> /opt/cherry_ai/.env")
                
            sftp.close()
            print(f"    ✓ {role} server configured")
            return True
            
        except Exception as e:
            print(f"    ❌ Failed to configure {role}: {e}")
            return False
        finally:
            ssh.close()
            
    def _copy_directory(self, sftp, ssh, local_dir: Path, remote_dir: str):
        """Recursively copy directory via SFTP"""
        ssh.exec_command(f"mkdir -p {remote_dir}")
        
        for item in local_dir.iterdir():
            if item.name.startswith('.') or item.name == '__pycache__':
                continue
                
            local_path = str(item)
            remote_path = f"{remote_dir}/{item.name}"
            
            if item.is_file():
                sftp.put(local_path, remote_path)
            elif item.is_dir():
                self._copy_directory(sftp, ssh, item, remote_path)
                
    def deploy_application(self):
        """Deploy application on servers"""
        print("\n🚀 Deploying application...")
        
        # Deploy database first
        db_server = self.deployment_info["database"]
        if not self.deploy_on_server(db_server["public_ip"], "database"):
            return False
            
        # TODO: Replace with asyncio.sleep() for async code
        # Wait for database to be ready
        time.sleep(30)
        
        # Deploy on app servers
        for i, server in enumerate(self.deployment_info["app_servers"]):
            if not self.deploy_on_server(server["public_ip"], f"app-{i}"):
                return False
                
        print("  ✓ Application deployed")
        return True
        
    def deploy_on_server(self, ip: str, role: str):
        """Deploy on individual server"""
        print(f"  Deploying on {role} server ({ip})...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            ip,
            username="root",
            key_filename=str(Path(self.ssh_key_path).expanduser())
        )
        
        try:
            # Start services based on role
            if role == "database":
                # Start database services
                commands = [
                    "cd /opt/cherry_ai",
                    "docker-compose up -d postgres redis weaviate",
                    "sleep 30",  # Wait for services
                    "docker-compose exec -T postgres psql -U postgres -c 'CREATE DATABASE cherry_ai;' || true"
                ]
            else:
                # Start application services
                commands = [
                    "cd /opt/cherry_ai",
                    "docker-compose up -d api admin-ui nginx"
                ]
                
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                stdout.read()
                
            print(f"    ✓ {role} deployment complete")
            return True
            
        except Exception as e:
            print(f"    ❌ Failed to deploy on {role}: {e}")
            return False
        finally:
            ssh.close()
            
    def health_check(self):
        """Run health checks on deployment"""
        print("\n🏥 Running health checks...")
        
        # Check load balancer
        lb_ip = self.deployment_info["load_balancer"]["ip"]
        
        # Check API health
        try:
            response = requests.get(f"http://{lb_ip}/health", timeout=10)
            if response.status_code == 200:
                print("  ✓ API health check passed")
            else:
                print(f"  ❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ API health check failed: {e}")
            return False
            
        # Check individual services
        for server in self.deployment_info["app_servers"]:
            if not self.check_server_health(server["public_ip"]):
                return False
                
        print("  ✓ All health checks passed")
        return True
        
    def check_server_health(self, ip: str):
        """Check health of individual server"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                ip,
                username="root",
                key_filename=str(Path(self.ssh_key_path).expanduser())
            )
            
            # Check Docker containers
            stdin, stdout, stderr = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}'")
            output = stdout.read().decode()
            
            if "Up" in output:
                return True
            else:
                print(f"  ⚠️  Some containers not running on {ip}")
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to check {ip}: {e}")
            return False
        finally:
            ssh.close()
            
    def print_access_info(self):
        """Print access information"""
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        
        lb_ip = self.deployment_info["load_balancer"]["ip"]
        
        print(f"\n📍 Access Points:")
        print(f"   API: http://{lb_ip}:8000")
        print(f"   Admin UI: http://{lb_ip}:8000/admin")
        print(f"   Grafana: http://{lb_ip}:3000")
        
        print(f"\n🔑 Credentials:")
        print(f"   API Key: {os.getenv('API_KEY', 'Check .env file')}")
        print(f"   Grafana: admin / {os.getenv('GRAFANA_PASSWORD', 'admin')}")
        
        print(f"\n🖥️  Server IPs:")
        print(f"   Database: {self.deployment_info['database']['public_ip']}")
        for i, server in enumerate(self.deployment_info['app_servers']):
            print(f"   App {i}: {server['public_ip']}")
            
        print(f"\n📝 Next Steps:")
        print(f"   1. Update DNS to point to {lb_ip}")
        print(f"   2. Configure SSL certificate")
        print(f"   3. Set up monitoring alerts")
        print(f"   4. Configure backup schedule")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    deployment = VultrDeployment()
    success = deployment.run()
    sys.exit(0 if success else 1)