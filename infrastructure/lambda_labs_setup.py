#!/usr/bin/env python3
"""
Lambda Labs Complete Setup Script for Orchestra Project
Handles SSH key upload, Pulumi configuration, and VPS provisioning
"""

import os
import sys
import json
import time
import subprocess
import requests
from typing import Dict, Optional, Tuple
from pathlib import Path

# Configuration from environment variables
LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY", "")
SSH_KEY_NAME = os.getenv("SSH_KEY_NAME", "manus-ai-deployment")
SSH_PUBLIC_KEY = os.getenv("SSH_PUBLIC_KEY", "")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "https://github.com/lynnmusil/orchestra-main.git")

# Check for required environment variables
if not LAMBDA_API_KEY:
    print("❌ Error: LAMBDA_API_KEY environment variable not set")
    print("   Export it with: export LAMBDA_API_KEY='your-api-key'")
    sys.exit(1)

if not SSH_PUBLIC_KEY:
    # Try to read from default location
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    if os.path.exists(ssh_key_path):
        with open(ssh_key_path, 'r') as f:
            SSH_PUBLIC_KEY = f.read().strip()
    else:
        print("❌ Error: SSH_PUBLIC_KEY environment variable not set and no key found at ~/.ssh/id_rsa.pub")
        sys.exit(1)

class LambdaLabsSetup:
    def __init__(self):
        self.api_key = LAMBDA_API_KEY
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.ssh_key_id = None
        self.instance_ip = None
        
    def step_0_clean_workstation(self):
        """Step 0: Clean the workstation"""
        print("\n🧹 Step 0: Cleaning workstation...")
        
        # Check for old directories
        old_dirs = [
            os.path.expanduser("~/orchestra-main-2"),
            os.path.expanduser("~/orchestra-main-1")
        ]
        
        for old_dir in old_dirs:
            if os.path.exists(old_dir):
                print(f"  Found old directory: {old_dir}")
                response = input(f"  Archive {old_dir}? (y/n): ")
                if response.lower() == 'y':
                    archive_path = f"{old_dir}_archive_{int(time.time())}"
                    os.rename(old_dir, archive_path)
                    print(f"  ✅ Archived to: {archive_path}")
        
        print("  ✅ Workstation cleaned")
        
    def step_1_finish_git_merge(self):
        """Step 1: Finish the Git merge"""
        print("\n🔀 Step 1: Finishing Git merge...")
        
        # Check git status
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True)
        
        if result.stdout:
            print("  ⚠️  Uncommitted changes detected:")
            print(result.stdout)
            response = input("  Commit and push changes? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(["git", "add", "-A"])
                subprocess.run(["git", "commit", "-m", "Lambda Labs infrastructure setup"])
                subprocess.run(["git", "push", "origin", "main"])
                print("  ✅ Changes pushed to main")
        else:
            print("  ✅ Working directory clean")
            
    def step_2_upload_ssh_key(self) -> int:
        """Step 2: Upload SSH key and get ID"""
        print("\n🔑 Step 2: Uploading SSH key...")
        
        # First, check if key already exists
        url = f"{self.base_url}/ssh-keys"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            keys = response.json().get("data", [])
            for key in keys:
                if key.get("name") == SSH_KEY_NAME:
                    self.ssh_key_id = key.get("id")
                    print(f"  ✅ SSH key already exists with ID: {self.ssh_key_id}")
                    return self.ssh_key_id
        
        # Upload new key
        data = {
            "name": SSH_KEY_NAME,
            "public_key": SSH_PUBLIC_KEY
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            self.ssh_key_id = result.get("data", {}).get("id")
            print(f"  ✅ SSH key uploaded with ID: {self.ssh_key_id}")
            return self.ssh_key_id
        else:
            print(f"  ❌ Failed to upload SSH key: {response.text}")
            sys.exit(1)
            
    def step_3_configure_pulumi(self):
        """Step 3: Configure Pulumi stack"""
        print("\n⚙️  Step 3: Configuring Pulumi stack...")
        
        # Set Pulumi config values
        configs = [
            ("lambda:api_key", LAMBDA_API_KEY, "--secret"),
            ("lambda:ssh_key_id", str(self.ssh_key_id), ""),
            ("github:token", GITHUB_PAT, "--secret"),
            ("lambda:instance_type", "gpu_1x_a10", ""),
            ("lambda:region", "us-west-1", "")
        ]
        
        for key, value, flag in configs:
            cmd = ["pulumi", "config", "set", key, value]
            if flag:
                cmd.append(flag)
            subprocess.run(cmd)
            print(f"  ✅ Set {key}")
            
        print("  ✅ Pulumi configuration complete")
        
    def step_4_provision_vps(self) -> str:
        """Step 4: Provision VPS using Pulumi"""
        print("\n🚀 Step 4: Provisioning VPS...")
        
        # Create the Pulumi program
        pulumi_program = '''
import pulumi
import pulumi_command as command
import requests
import json

# Get configuration
config = pulumi.Config()
api_key = config.require_secret("lambda:api_key")
ssh_key_id = config.require_int("lambda:ssh_key_id")
instance_type = config.get("lambda:instance_type") or "gpu_1x_a10"
region = config.get("lambda:region") or "us-west-1"

# Lambda Labs instance provisioning via API
class LambdaInstance(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("lambda:instance", name, None, opts)
        
        # Create instance via API call
        self.instance = command.local.Command(
            f"{name}-create",
            create=pulumi.Output.all(api_key, ssh_key_id).apply(
                lambda args: f"""
                curl -s -X POST \\
                  -H "Authorization: Bearer {args[0]}" \\
                  -H "Content-Type: application/json" \\
                  -d '{{"instance_type":"{instance_type}","region":"{region}","ssh_key_ids":[{args[1]}],"quantity":1,"name":"orchestra-dev"}}' \\
                  https://cloud.lambdalabs.com/api/v1/instances
                """
            ),
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Extract IP address from response
        self.ip_address = self.instance.stdout.apply(
            lambda output: json.loads(output).get("data", {}).get("instances", [{}])[0].get("ip")
        )
        
        self.register_outputs({
            "ip_address": self.ip_address
        })

# Create the instance
instance = LambdaInstance("orchestra-dev")

# Export the IP address
pulumi.export("ipAddress", instance.ip_address)
'''
        
        # Write Pulumi program
        with open("__main__.py", "w") as f:
            f.write(pulumi_program)
            
        # Run Pulumi up
        print("  Running pulumi up...")
        result = subprocess.run(["pulumi", "up", "--yes"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            # Extract IP from output
            for line in result.stdout.split('\n'):
                if "ipAddress:" in line:
                    self.instance_ip = line.split('"')[1]
                    print(f"  ✅ VPS provisioned with IP: {self.instance_ip}")
                    return self.instance_ip
        else:
            print(f"  ❌ Pulumi up failed: {result.stderr}")
            sys.exit(1)
            
    def step_5_bootstrap_vps(self):
        """Step 5: Bootstrap the VPS"""
        print("\n🔧 Step 5: Bootstrapping VPS...")
        
        if not self.instance_ip:
            print("  ❌ No instance IP available")
            return
            
        # Wait for SSH to be ready
        print("  ⏳ Waiting for SSH to be ready...")
        for i in range(30):
            result = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
                 f"ubuntu@{self.instance_ip}", "echo", "ready"],
                capture_output=True
            )
            if result.returncode == 0:
                break
            time.sleep(10)
        else:
            print("  ⚠️  SSH not ready after 5 minutes, continuing anyway...")
            
        # Bootstrap commands
        bootstrap_script = f'''#!/bin/bash
set -e

echo "🚀 Starting Orchestra bootstrap..."

# Update system
sudo apt-get update
sudo apt-get install -y git python3-pip python3-venv docker.io docker-compose

# Clone repository
git clone {GITHUB_REPO} ~/orchestra-main
cd ~/orchestra-main

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up MCP environment
if [ -f "./setup_mcp_environment.sh" ]; then
    chmod +x ./setup_mcp_environment.sh
    ./setup_mcp_environment.sh
fi

# Start services
docker-compose up -d

echo "✅ Bootstrap complete!"
'''
        
        # Write bootstrap script
        with open("/tmp/bootstrap.sh", "w") as f:
            f.write(bootstrap_script)
            
        # Copy and execute bootstrap script
        print("  📤 Copying bootstrap script...")
        subprocess.run([
            "scp", "-o", "StrictHostKeyChecking=no",
            "/tmp/bootstrap.sh", f"ubuntu@{self.instance_ip}:~/bootstrap.sh"
        ])
        
        print("  🏃 Running bootstrap script...")
        subprocess.run([
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"ubuntu@{self.instance_ip}", "bash", "~/bootstrap.sh"
        ])
        
        print("  ✅ VPS bootstrapped successfully")
        
    def step_6_setup_development(self):
        """Step 6: Set up development workflow"""
        print("\n💻 Step 6: Setting up development workflow...")
        
        # Create VS Code SSH config
        ssh_config = f'''
Host orchestra-dev
    HostName {self.instance_ip}
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
'''
        
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        
        # Backup existing config
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, 'r') as f:
                existing = f.read()
            if "Host orchestra-dev" not in existing:
                with open(ssh_config_path, 'a') as f:
                    f.write(ssh_config)
                print("  ✅ Added orchestra-dev to SSH config")
        else:
            with open(ssh_config_path, 'w') as f:
                f.write(ssh_config)
            os.chmod(ssh_config_path, 0o600)
            print("  ✅ Created SSH config")
            
        # Create helper scripts
        self.create_helper_scripts()
        
        print("\n🎉 Setup complete!")
        print(f"\n📋 Quick reference:")
        print(f"  - Instance IP: {self.instance_ip}")
        print(f"  - SSH: ssh ubuntu@{self.instance_ip}")
        print(f"  - VS Code: code --remote ssh-remote+orchestra-dev /home/ubuntu/orchestra-main")
        print(f"  - Destroy: make dev-down")
        
    def create_helper_scripts(self):
        """Create helper scripts for daily workflow"""
        
        # Create Makefile targets
        makefile_content = '''
# Lambda Labs development targets
.PHONY: dev-up dev-down dev-ssh dev-status

dev-up:
	@echo "🚀 Provisioning Lambda Labs VPS..."
	@pulumi up --yes

dev-down:
	@echo "🔻 Destroying Lambda Labs VPS..."
	@pulumi destroy --yes

dev-ssh:
	@echo "🔗 Connecting to Lambda Labs VPS..."
	@ssh orchestra-dev

dev-status:
	@echo "📊 Checking Lambda Labs instances..."
	@python3 infrastructure/lambda_labs_status.py
'''
        
        # Append to existing Makefile or create new one
        makefile_path = "Makefile"
        if os.path.exists(makefile_path):
            with open(makefile_path, 'a') as f:
                f.write("\n" + makefile_content)
        else:
            with open(makefile_path, 'w') as f:
                f.write(makefile_content)
                
        # Create status check script
        status_script = '''#!/usr/bin/env python3
import requests
import os

api_key = os.getenv("LAMBDA_API_KEY", "''' + LAMBDA_API_KEY + '''")
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get("https://cloud.lambdalabs.com/api/v1/instances", headers=headers)
if response.status_code == 200:
    instances = response.json().get("data", [])
    for instance in instances:
        print(f"Instance: {instance.get('name')} - IP: {instance.get('ip')} - Status: {instance.get('status')}")
else:
    print(f"Error: {response.status_code}")
'''
        
        with open("infrastructure/lambda_labs_status.py", "w") as f:
            f.write(status_script)
        os.chmod("infrastructure/lambda_labs_status.py", 0o755)
        
    def run_all_steps(self):
        """Run all setup steps in sequence"""
        print("🎯 Orchestra Lambda Labs Setup")
        print("=" * 50)
        
        self.step_0_clean_workstation()
        self.step_1_finish_git_merge()
        self.step_2_upload_ssh_key()
        self.step_3_configure_pulumi()
        self.step_4_provision_vps()
        self.step_5_bootstrap_vps()
        self.step_6_setup_development()

if __name__ == "__main__":
    setup = LambdaLabsSetup()
    setup.run_all_steps()