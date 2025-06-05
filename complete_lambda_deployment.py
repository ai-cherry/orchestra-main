#!/usr/bin/env python3
"""
Complete the Lambda Labs deployment that was interrupted
"""

import subprocess
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def execute_ssh_command(command: str, server_ip: str = "150.136.94.139", username: str = "ubuntu") -> tuple:
    """Execute command via SSH"""
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {username}@{server_ip} '{command}'"
    logger.debug(f"Executing: {command}")
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    logger.info("🔧 Completing Lambda Labs deployment...")
    logger.info("=" * 60)
    
    server_ip = "150.136.94.139"
    username = "ubuntu"
    remote_app_dir = "/opt/orchestra"
    
    # Step 1: Check PostgreSQL and start if needed
    logger.info("\n📍 Step 1: Checking PostgreSQL...")
    exit_code, stdout, stderr = execute_ssh_command("sudo systemctl status postgresql")
    if exit_code != 0:
        logger.info("Starting PostgreSQL...")
        execute_ssh_command("sudo systemctl start postgresql")
        execute_ssh_command("sudo systemctl enable postgresql")
    else:
        logger.info("✅ PostgreSQL is already running")
    
    # Step 2: Update requirements.txt on server
    logger.info("\n📍 Step 2: Updating requirements.txt...")
    scp_cmd = f"scp requirements.txt {username}@{server_ip}:{remote_app_dir}/"
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✅ Updated requirements.txt")
    else:
        logger.error(f"Failed to copy requirements.txt: {result.stderr}")
    
    # Step 3: Install dependencies
    logger.info("\n📍 Step 3: Installing dependencies...")
    exit_code, stdout, stderr = execute_ssh_command(
        f"cd {remote_app_dir} && source venv/bin/activate && pip install -r requirements.txt"
    )
    if exit_code == 0:
        logger.info("✅ Dependencies installed successfully")
    else:
        logger.error(f"Dependency installation failed: {stderr}")
        # Try to continue anyway
    
    # Step 4: Copy .env file
    logger.info("\n📍 Step 4: Copying environment configuration...")
    scp_cmd = f"scp .env {username}@{server_ip}:{remote_app_dir}/"
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✅ Environment configuration copied")
    else:
        logger.warning("Could not copy .env file, using template")
        execute_ssh_command(f"cd {remote_app_dir} && cp .env.template .env")
    
    # Step 5: Create systemd service
    logger.info("\n📍 Step 5: Creating systemd service...")
    service_content = f"""[Unit]
Description=Orchestra API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User={username}
WorkingDirectory={remote_app_dir}
Environment="PATH={remote_app_dir}/venv/bin:/usr/local/bin:/usr/bin"
ExecStart={remote_app_dir}/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Write service file locally
    with open("/tmp/orchestra-api.service", "w") as f:
        f.write(service_content)
    
    # Copy to server
    scp_cmd = f"scp /tmp/orchestra-api.service {username}@{server_ip}:/tmp/"
    subprocess.run(scp_cmd, shell=True)
    
    # Install service
    execute_ssh_command("sudo mv /tmp/orchestra-api.service /etc/systemd/system/")
    execute_ssh_command("sudo systemctl daemon-reload")
    execute_ssh_command("sudo systemctl enable orchestra-api")
    logger.info("✅ Service configured")
    
    # Step 6: Start the service
    logger.info("\n📍 Step 6: Starting Orchestra service...")
    execute_ssh_command("sudo systemctl stop orchestra-api 2>/dev/null")  # Stop if running
    exit_code, stdout, stderr = execute_ssh_command("sudo systemctl start orchestra-api")
    
    if exit_code == 0:
        logger.info("✅ Service started")
    else:
        logger.error(f"Service start failed: {stderr}")
        # Get logs
        _, logs, _ = execute_ssh_command("sudo journalctl -u orchestra-api -n 50")
        logger.error(f"Service logs:\n{logs}")
    
    # Step 7: Verify deployment
    logger.info("\n📍 Step 7: Verifying deployment...")
    import time
    time.sleep(5)  # Wait for service to fully start
    
    # Check service status
    exit_code, stdout, _ = execute_ssh_command("sudo systemctl is-active orchestra-api")
    if exit_code == 0:
        logger.info("✅ Service is active")
    else:
        logger.error("❌ Service is not active")
    
    # Check API health
    exit_code, stdout, stderr = execute_ssh_command("curl -s http://localhost:8000/health || echo 'API not responding'")
    if "API not responding" not in stdout and exit_code == 0:
        logger.info("✅ API is responding")
        logger.info(f"Response: {stdout}")
    else:
        logger.error("❌ API is not responding")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Deployment completion finished!")
    logger.info(f"🌐 Server: {server_ip}")
    logger.info("\n📝 Next steps:")
    logger.info("1. SSH to server: ssh ubuntu@150.136.94.139")
    logger.info("2. Check logs: sudo journalctl -u orchestra-api -f")
    logger.info("3. Update .env with production values if needed")
    logger.info("4. Configure SSL certificates for HTTPS")
    logger.info("5. Set up monitoring and alerts")

if __name__ == "__main__":
    main()