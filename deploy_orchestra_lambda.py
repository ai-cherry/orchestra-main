#!/usr/bin/env python3
"""
Orchestra Lambda Labs Deployment Script
Deploys to existing Lambda Labs infrastructure via SSH
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'lambda_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class LambdaLabsDeployer:
    """Deploy Orchestra to Lambda Labs infrastructure"""
    
    def __init__(self):
        self.server_ip = "150.136.94.139"
        self.username = "ubuntu"
        self.ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
        self.remote_app_dir = "/opt/orchestra"
        self.deployment_log = []
        
        # Load deployment strategy
        if os.path.exists("lambda_deployment_strategy.json"):
            with open("lambda_deployment_strategy.json", "r") as f:
                self.strategy = json.load(f)
                logger.info("✅ Loaded deployment strategy")
        else:
            logger.warning("⚠️  No deployment strategy found, using defaults")
            self.strategy = self._default_strategy()
    
    def _default_strategy(self) -> Dict[str, Any]:
        """Default deployment strategy for Lambda Labs"""
        return {
            "deployment_type": "SSH-based deployment to existing Lambda Labs instance",
            "target_server": {
                "ip": self.server_ip,
                "provider": "Lambda Labs",
                "specs": "8x A100 GPU instance",
                "os": "Ubuntu 22.04 LTS"
            },
            "existing_services": {
                "postgresql": "localhost:5432",
                "redis": "localhost:6379",
                "weaviate": "localhost:8080",
                "api": "localhost:8000"
            }
        }
    
    def _log_deployment(self, message: str, status: str, details: Any = None):
        """Log deployment step"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "status": status,
            "details": details
        }
        self.deployment_log.append(entry)
        
    def execute_ssh_command(self, command: str) -> tuple:
        """Execute command via SSH"""
        ssh_cmd = f"ssh -o StrictHostKeyChecking=no {self.username}@{self.server_ip} '{command}'"
        
        logger.debug(f"Executing: {command}")
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        
        return result.returncode, result.stdout, result.stderr
    
    def check_ssh_connection(self) -> bool:
        """Test SSH connection to Lambda Labs server"""
        logger.info(f"🔌 Testing SSH connection to {self.server_ip}...")
        
        exit_code, stdout, stderr = self.execute_ssh_command("echo 'SSH connection successful'")
        
        if exit_code == 0:
            logger.info("✅ SSH connection established")
            self._log_deployment("SSH connection established", "success")
            return True
        else:
            logger.error(f"❌ SSH connection failed: {stderr}")
            logger.info("\nTo fix SSH connection:")
            logger.info("1. Ensure you have SSH access to the Lambda Labs instance")
            logger.info("2. Run: ssh-copy-id ubuntu@150.136.94.139")
            logger.info("3. Or set LAMBDA_SSH_PASSWORD environment variable")
            self._log_deployment(f"SSH connection failed: {stderr}", "error")
            return False
    
    def check_existing_services(self) -> Dict[str, bool]:
        """Check status of existing services"""
        logger.info("🔍 Checking existing services...")
        
        services_status = {}
        
        # Check PostgreSQL
        exit_code, _, _ = self.execute_ssh_command("sudo -u postgres psql -c 'SELECT 1;' 2>/dev/null")
        services_status['postgresql'] = exit_code == 0
        logger.info(f"  PostgreSQL: {'✅ Running' if services_status['postgresql'] else '❌ Not running'}")
        
        # Check Redis
        exit_code, stdout, _ = self.execute_ssh_command("redis-cli ping 2>/dev/null")
        services_status['redis'] = exit_code == 0 and "PONG" in stdout
        logger.info(f"  Redis: {'✅ Running' if services_status['redis'] else '❌ Not running'}")
        
        # Check Weaviate
        exit_code, _, _ = self.execute_ssh_command("curl -s http://localhost:8080/v1/.well-known/ready 2>/dev/null")
        services_status['weaviate'] = exit_code == 0
        logger.info(f"  Weaviate: {'✅ Running' if services_status['weaviate'] else '❌ Not running'}")
        
        # Check Nginx
        exit_code, _, _ = self.execute_ssh_command("systemctl is-active nginx")
        services_status['nginx'] = exit_code == 0
        logger.info(f"  Nginx: {'✅ Running' if services_status['nginx'] else '❌ Not running'}")
        
        self._log_deployment("Service check completed", "info", services_status)
        return services_status
    
    def prepare_deployment_directory(self) -> bool:
        """Prepare the deployment directory"""
        logger.info("📁 Preparing deployment directory...")
        
        # Create directory
        exit_code, _, stderr = self.execute_ssh_command(f"sudo mkdir -p {self.remote_app_dir}")
        if exit_code != 0:
            logger.error(f"Failed to create directory: {stderr}")
            return False
        
        # Set ownership
        exit_code, _, stderr = self.execute_ssh_command(
            f"sudo chown -R {self.username}:{self.username} {self.remote_app_dir}"
        )
        if exit_code != 0:
            logger.error(f"Failed to set ownership: {stderr}")
            return False
        
        logger.info(f"✅ Directory {self.remote_app_dir} is ready")
        return True
    
    def deploy_files(self) -> bool:
        """Deploy files to Lambda Labs server"""
        logger.info("📤 Deploying files...")
        
        # Create a deployment package
        files_to_deploy = [
            "cherry-ai-orchestrator-final.html",
            "cherry-ai-orchestrator-enhanced.js",
            "cherry-ai-orchestrator.js",
            "main.py",
            "fixed_main_app.py",
            "lambda_infrastructure_mcp_server.py",
            ".env.template"
        ]
        
        # Check which files exist locally
        existing_files = []
        for file in files_to_deploy:
            if os.path.exists(file):
                existing_files.append(file)
                logger.debug(f"  Found: {file}")
            else:
                logger.warning(f"  Missing: {file}")
        
        if not existing_files:
            logger.error("No deployable files found!")
            return False
        
        # Use rsync to deploy files
        exclude_patterns = [".git", "__pycache__", "*.pyc", ".env", "node_modules", "venv"]
        exclude_args = " ".join([f"--exclude='{p}'" for p in exclude_patterns])
        
        rsync_cmd = f"rsync -avz {exclude_args} . {self.username}@{self.server_ip}:{self.remote_app_dir}/"
        
        logger.info(f"Syncing files to {self.server_ip}:{self.remote_app_dir}")
        result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Files deployed successfully")
            self._log_deployment("Files deployed", "success", {"files": existing_files})
            return True
        else:
            logger.error(f"❌ Deployment failed: {result.stderr}")
            self._log_deployment("File deployment failed", "error", {"error": result.stderr})
            return False
    
    def configure_nginx(self) -> bool:
        """Configure nginx for Orchestra"""
        logger.info("🌐 Configuring nginx...")
        
        nginx_config = """server {
    listen 80;
    server_name _;
    
    location /orchestrator {
        alias /opt/orchestra;
        try_files $uri $uri/ /cherry-ai-orchestrator-final.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}"""
        
        # Write config to temp file
        temp_config = "/tmp/orchestra-nginx.conf"
        with open(temp_config, "w") as f:
            f.write(nginx_config)
        
        # Copy to server
        scp_cmd = f"scp {temp_config} {self.username}@{self.server_ip}:/tmp/"
        subprocess.run(scp_cmd, shell=True)
        
        # Install nginx config
        commands = [
            "sudo cp /tmp/orchestra-nginx.conf /etc/nginx/sites-available/orchestra",
            "sudo ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/",
            "sudo nginx -t",
            "sudo systemctl reload nginx"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_ssh_command(cmd)
            if exit_code != 0:
                logger.error(f"Failed: {cmd} - {stderr}")
                return False
        
        logger.info("✅ Nginx configured")
        return True
    
    def setup_systemd_service(self) -> bool:
        """Setup systemd service for Orchestra API"""
        logger.info("🔧 Setting up systemd service...")
        
        service_config = """[Unit]
Description=Orchestra API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/orchestra
Environment="PYTHONPATH=/opt/orchestra"
ExecStart=/usr/bin/python3 /opt/orchestra/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        
        # Write service file
        temp_service = "/tmp/orchestra-api.service"
        with open(temp_service, "w") as f:
            f.write(service_config)
        
        # Copy to server
        scp_cmd = f"scp {temp_service} {self.username}@{self.server_ip}:/tmp/"
        subprocess.run(scp_cmd, shell=True)
        
        # Install service
        commands = [
            "sudo cp /tmp/orchestra-api.service /etc/systemd/system/",
            "sudo systemctl daemon-reload",
            "sudo systemctl enable orchestra-api"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_ssh_command(cmd)
            if exit_code != 0:
                logger.error(f"Failed: {cmd} - {stderr}")
                return False
        
        logger.info("✅ Systemd service configured")
        return True
    
    def deploy(self) -> bool:
        """Run full deployment process"""
        logger.info("🚀 ORCHESTRA DEPLOYMENT TO LAMBDA LABS")
        logger.info(f"Target: {self.username}@{self.server_ip}")
        logger.info("=" * 60)
        
        # Check SSH connection
        if not self.check_ssh_connection():
            return False
        
        # Check existing services
        service_status = self.check_existing_services()
        
        # Prepare deployment directory
        if not self.prepare_deployment_directory():
            return False
        
        # Deploy files
        if not self.deploy_files():
            return False
        
        # Configure nginx
        self.configure_nginx()
        
        # Setup systemd service
        self.setup_systemd_service()
        
        # Save deployment log
        log_file = f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump({
                "deployment": self.deployment_log,
                "services": service_status,
                "strategy": self.strategy
            }, f, indent=2)
        
        logger.info(f"\n📄 Deployment log saved to: {log_file}")
        logger.info("\n✅ DEPLOYMENT COMPLETE!")
        logger.info(f"Access Orchestra at: http://{self.server_ip}/orchestrator/")
        logger.info("\n⚠️  Next steps:")
        logger.info("1. Update .env file on server with actual values")
        logger.info("2. Run database migrations if needed")
        logger.info("3. Start the Orchestra API service: sudo systemctl start orchestra-api")
        logger.info("4. Configure SSL certificates for HTTPS")
        
        return True

def main():
    """Main entry point"""
    deployer = LambdaLabsDeployer()
    
    # Check for required files
    if not os.path.exists("cherry-ai-orchestrator-final.html"):
        logger.error("❌ cherry-ai-orchestrator-final.html not found!")
        logger.info("Make sure you're running this from the project root directory")
        sys.exit(1)
    
    # Run deployment
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()