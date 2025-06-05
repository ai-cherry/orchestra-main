#!/usr/bin/env python3
"""
Setup and execute Vultr deployment
Handles API key configuration and runs deployment
"""

import os
import sys
import subprocess
from pathlib import Path
import getpass

def setup_vultr_api_key():
    """Setup Vultr API key"""
    print("🔑 Vultr API Key Setup")
    print("=" * 50)
    
    # Check if already set
    if os.getenv("VULTR_API_KEY"):
        print("✓ VULTR_API_KEY already set in environment")
        return True
        
    # Read from .env
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
VULTR_API_KEY = os.getenv("SCRIPT_SETUP_VULTR_DEPLOYMENT_API_KEY", "")
                if api_key:
                    os.environ["VULTR_API_KEY"] = api_key
                    print("✓ VULTR_API_KEY loaded from .env file")
                    return True
                    
    # Ask user for API key
    print("\n⚠️  VULTR_API_KEY not found!")
    print("\nTo get your Vultr API key:")
    print("1. Log in to https://my.vultr.com/")
    print("2. Go to Account → API")
    print("3. Create a new API key with full permissions")
    print("4. Copy the key (it will only be shown once)")
    
    api_key = getpass.getpass("\nEnter your Vultr API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
        
    # Update .env file
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
            
        updated = False
        for i, line in enumerate(lines):
VULTR_API_KEY = os.getenv("SCRIPT_SETUP_VULTR_DEPLOYMENT_API_KEY", "")
                updated = True
                break
                
        if updated:
            with open(env_path, "w") as f:
                f.writelines(lines)
            print("✓ Updated VULTR_API_KEY in .env file")
        else:
            print("❌ Could not find VULTR_API_KEY line in .env file")
            return False
            
    # Set in environment
    os.environ["VULTR_API_KEY"] = api_key
    return True

def check_prerequisites():
    """Check deployment prerequisites"""
    print("\n📋 Checking Prerequisites")
    print("=" * 50)
    
    checks = []
    
    # Check Python packages
    try:
        import requests
        checks.append(("✓", "requests package installed"))
    except ImportError:
        checks.append(("❌", "requests package missing - run: pip install requests"))
        
    try:
        import paramiko
        checks.append(("✓", "paramiko package installed"))
    except ImportError:
        checks.append(("❌", "paramiko package missing - run: pip install paramiko"))
        
    # Check SSH key
    ssh_key_path = Path.home() / ".ssh/cherry_ai_deploy"
    if ssh_key_path.exists():
        checks.append(("✓", "SSH key exists"))
    else:
        checks.append(("⚠️", "SSH key will be generated"))
        
    # Check git
    result = subprocess.run(["which", "git"], capture_output=True)
    if result.returncode == 0:
        checks.append(("✓", "git installed"))
    else:
        checks.append(("❌", "git not installed"))
        
    # Print results
    all_good = True
    for status, message in checks:
        print(f"{status} {message}")
        if status == "❌":
            all_good = False
            
    return all_good

def run_deployment():
    """Run the deployment script"""
    print("\n🚀 Starting Deployment")
    print("=" * 50)
    
    deployment_script = Path("scripts/vultr_direct_deploy.py")
    
    if not deployment_script.exists():
        print("❌ Deployment script not found: scripts/vultr_direct_deploy.py")
        return False
        
    # Make executable
    deployment_script.chmod(0o755)
    
    # Run deployment
    try:
        subprocess.run([sys.executable, str(deployment_script)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Deployment failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        return False

def main():
    """Main setup and deployment flow"""
    print("🎯 cherry_ai MCP Vultr Deployment Setup")
    print("=" * 50)
    
    # Setup API key
    if not setup_vultr_api_key():
        print("\n❌ Cannot proceed without Vultr API key")
        sys.exit(1)
        
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Please fix the issues above before proceeding")
        sys.exit(1)
        
    # Confirm deployment
    print("\n⚠️  DEPLOYMENT CONFIRMATION")
    print("=" * 50)
    print("This will create the following resources on Vultr:")
    print("- 1 VPC network")
    print("- 1 Firewall group with security rules")
    print("- 1 Database server (4 vCPU, 8GB RAM)")
    print("- 2 Application servers (2 vCPU, 4GB RAM each)")
    print("- 1 Load balancer")
    print("\nEstimated monthly cost: ~$100-150")
    
    response = input("\nProceed with deployment? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("\n❌ Deployment cancelled")
        sys.exit(0)
        
    # Run deployment
    if run_deployment():
        print("\n✅ Deployment completed successfully!")
    else:
        print("\n❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()