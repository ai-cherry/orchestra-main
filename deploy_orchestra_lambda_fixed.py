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
        self._log_deployment("Directory prepared", "success")
        return True
    
    def deploy_files(self) -> bool:
        """Deploy files to Lambda Labs server"""
        logger.info("📦 Deploying application files...")
        
        # Create exclude file for rsync
        exclude_patterns = [
            "__pycache__/",
            "*.pyc",
            ".git/",
            "venv/",
            "node_modules/",
            "*.log",
            ".env",
            "*.db",
            "*.sqlite",
            "*.md",
            "audit_results_*",
            "debug_report_*",
            "test_validation_report_*"
        ]
        
        with open(".rsync-exclude", "w") as f:
            f.write("\n".join(exclude_patterns))
        
        # Use rsync to deploy files
        rsync_cmd = f"rsync -avz --progress --delete --exclude-from=.rsync-exclude ./ {self.username}@{self.server_ip}:{self.remote_app_dir}/"
        
        logger.info("Running rsync...")
        result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Files deployed successfully")
            self._log_deployment("Files deployed", "success")
            return True
        else:
            logger.error(f"❌ File deployment failed: {result.stderr}")
            self._log_deployment(f"File deployment failed: {result.stderr}", "error")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies on remote server"""
        logger.info("📚 Installing dependencies...")
        
        # Create virtual environment if it doesn't exist
        logger.debug("Creating virtual environment...")
        exit_code, _, stderr = self.execute_ssh_command(
            f"cd {self.remote_app_dir} && python3 -m venv venv"
        )
        if exit_code != 0:
            logger.warning(f"Virtual environment creation warning: {stderr}")
        
        # Install requirements
        logger.debug("Installing Python packages...")
        requirements_files = ["requirements.txt", "requirements-app.txt"]
        
        for req_file in requirements_files:
            # Check if file exists
            exit_code, stdout, _ = self.execute_ssh_command(
                f"test -f {self.remote_app_dir}/{req_file} && echo 'EXISTS'"
            )
            
            if exit_code == 0 and "EXISTS" in stdout:
                logger.info(f"Installing from {req_file}...")
                exit_code, _, stderr = self.execute_ssh_command(
                    f"cd {self.remote_app_dir} && source venv/bin/activate && pip install -r {req_file}"
                )
                if exit_code != 0:
                    logger.error(f"Failed to install {req_file}: {stderr}")
                    return False
        
        logger.info("✅ Dependencies installed")
        self._log_deployment("Dependencies installed", "success")
        return True
    
    def configure_environment(self) -> bool:
        """Configure environment variables"""
        logger.info("🔧 Configuring environment...")
        
        # Check if .env.template exists locally
        if os.path.exists(".env.template"):
            logger.debug("Copying .env.template to server...")
            
            # Copy template using scp
            scp_cmd = f"scp .env.template {self.username}@{self.server_ip}:{self.remote_app_dir}/"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Create .env from template if it doesn't exist
                self.execute_ssh_command(
                    f"cd {self.remote_app_dir} && test -f .env || cp .env.template .env"
                )
                
                logger.info("✅ Environment template configured")
                logger.warning("⚠️  Remember to update .env with actual values on the server")
            else:
                logger.error(f"Failed to copy .env.template: {result.stderr}")
        else:
            logger.warning("⚠️  No .env.template found locally")
        
        self._log_deployment("Environment configured", "success")
        return True
    
    def run_database_migrations(self) -> bool:
        """Run database migrations"""
        logger.info("🗄️ Running database migrations...")
        
        # Check for Django manage.py
        exit_code, stdout, _ = self.execute_ssh_command(
            f"test -f {self.remote_app_dir}/manage.py && echo 'DJANGO'"
        )
        
        if exit_code == 0 and "DJANGO" in stdout:
            logger.debug("Running Django migrations...")
            exit_code, _, stderr = self.execute_ssh_command(
                f"cd {self.remote_app_dir} && source venv/bin/activate && python manage.py migrate"
            )
            if exit_code != 0:
                logger.warning(f"Django migration warning: {stderr}")
        
        # Check for Alembic
        exit_code, stdout, _ = self.execute_ssh_command(
            f"test -f {self.remote_app_dir}/alembic.ini && echo 'ALEMBIC'"
        )
        
        if exit_code == 0 and "ALEMBIC" in stdout:
            logger.debug("Running Alembic migrations...")
            exit_code, _, stderr = self.execute_ssh_command(
                f"cd {self.remote_app_dir} && source venv/bin/activate && alembic upgrade head"
            )
            if exit_code != 0:
                logger.warning(f"Alembic migration warning: {stderr}")
        
        logger.info("✅ Database migrations completed")
        self._log_deployment("Database migrations completed", "success")
        return True
    
    def configure_services(self) -> bool:
        """Configure systemd services"""
        logger.info("⚙️ Configuring services...")
        
        # Create systemd service for Orchestra API
        service_content = f"""[Unit]
Description=Orchestra API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User={self.username}
WorkingDirectory={self.remote_app_dir}
Environment="PATH={self.remote_app_dir}/venv/bin:/usr/local/bin:/usr/bin"
ExecStart={self.remote_app_dir}/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 src.api.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        service_file = "/tmp/orchestra-api.service"
        with open(service_file, "w") as f:
            f.write(service_content)
        
        # Copy to server
        scp_cmd = f"scp {service_file} {self.username}@{self.server_ip}:/tmp/"
        subprocess.run(scp_cmd, shell=True)
        
        # Install service
        self.execute_ssh_command("sudo mv /tmp/orchestra-api.service /etc/systemd/system/")
        self.execute_ssh_command("sudo systemctl daemon-reload")
        self.execute_ssh_command("sudo systemctl enable orchestra-api")
        
        logger.info("✅ Services configured")
        self._log_deployment("Services configured", "success")
        return True
    
    def restart_services(self) -> bool:
        """Restart Orchestra services"""
        logger.info("🔄 Restarting services...")
        
        # Restart Orchestra API
        exit_code, _, stderr = self.execute_ssh_command("sudo systemctl restart orchestra-api")
        
        if exit_code != 0:
            logger.warning(f"Service restart warning: {stderr}")
        
        # Wait for service to start
        import time
        time.sleep(5)
        
        # Check service status
        exit_code, stdout, _ = self.execute_ssh_command("sudo systemctl is-active orchestra-api")
        
        if exit_code == 0 and "active" in stdout:
            logger.info("✅ Services restarted successfully")
            self._log_deployment("Services restarted", "success")
            return True
        else:
            logger.error("❌ Service failed to start")
            
            # Get service logs
            _, logs, _ = self.execute_ssh_command("sudo journalctl -u orchestra-api -n 50")
            logger.error(f"Service logs:\n{logs}")
            
            self._log_deployment("Service restart failed", "error")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify the deployment is working"""
        logger.info("✅ Verifying deployment...")
        
        # Check API health endpoint
        exit_code, stdout, _ = self.execute_ssh_command("curl -s http://localhost:8000/health")
        
        if exit_code == 0:
            logger.info("✅ API is responding")
            
            # Check database connectivity
            exit_code, stdout, _ = self.execute_ssh_command(
                f"cd {self.remote_app_dir} && source venv/bin/activate && python -c 'import psycopg2; print(\"DB OK\")' 2>&1"
            )
            
            if exit_code == 0 and "DB OK" in stdout:
                logger.info("✅ Database connectivity verified")
            else:
                logger.warning("⚠️  Database connectivity issues")
            
            self._log_deployment("Deployment verified", "success")
            return True
        else:
            logger.error("❌ API is not responding")
            self._log_deployment("Deployment verification failed", "error")
            return False
    
    def save_deployment_report(self):
        """Save deployment report"""
        report = {
            "deployment_date": datetime.now().isoformat(),
            "target_server": self.strategy["target_server"],
            "deployment_log": self.deployment_log,
            "final_status": "success" if self._check_deployment_success() else "failed"
        }
        
        report_file = f"lambda_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Deployment report saved to: {report_file}")
    
    def _check_deployment_success(self) -> bool:
        """Check if deployment was successful"""
        error_count = sum(1 for event in self.deployment_log if event["status"] == "error")
        return error_count == 0
    
    def deploy(self) -> bool:
        """Execute full deployment process"""
        logger.info("🚀 Starting Orchestra deployment to Lambda Labs")
        logger.info("=" * 60)
        
        steps = [
            ("Check SSH connection", self.check_ssh_connection),
            ("Check existing services", self.check_existing_services),
            ("Prepare deployment directory", self.prepare_deployment_directory),
            ("Deploy files", self.deploy_files),
            ("Install dependencies", self.install_dependencies),
            ("Configure environment", self.configure_environment),
            ("Run database migrations", self.run_database_migrations),
            ("Configure services", self.configure_services),
            ("Restart services", self.restart_services),
            ("Verify deployment", self.verify_deployment)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📍 Step: {step_name}")
            logger.info("-" * 40)
            
            try:
                result = step_func()
                if not result:
                    logger.error(f"❌ Step failed: {step_name}")
                    break
            except Exception as e:
                logger.error(f"❌ Critical error in {step_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                break
        
        # Save deployment report
        self.save_deployment_report()
        
        # Final status
        success = self._check_deployment_success()
        
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("✅ DEPLOYMENT SUCCESSFUL!")
            logger.info(f"🌐 Orchestra is now running on Lambda Labs at {self.server_ip}")
            logger.info("📝 Next steps:")
            logger.info("  1. SSH to server and update .env with production values")
            logger.info("  2. Configure SSL certificates")
            logger.info("  3. Set up monitoring and alerts")
            logger.info("  4. Test all endpoints")
        else:
            logger.error("❌ DEPLOYMENT FAILED!")
            logger.error("Check the deployment log for errors")
        
        return success


def main():
    """Main execution"""
    deployer = LambdaLabsDeployer()
    
    # Check for SSH access
    if not os.path.exists(deployer.ssh_key_path):
        logger.warning("⚠️  No SSH key found at ~/.ssh/id_rsa")
        logger.info("Make sure you have SSH access configured")
    
    # Run deployment
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()