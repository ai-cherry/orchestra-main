#!/usr/bin/env python3
"""
Upload and deploy Cherry AI collaboration bridge via HTTP
"""

import requests
import base64
import json

# Server details
SERVER_IP = "45.32.69.157"
SERVER_URL = f"http://{SERVER_IP}"

def create_deployment_package():
    """Create a base64 encoded deployment package"""
    files_to_deploy = {
        "cherry_ai_live_collaboration_bridge.py": open("cherry_ai_live_collaboration_bridge.py", "r").read(),
        "deploy_collaboration_bridge.py": open("deploy_collaboration_bridge.py", "r").read()
    }
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Cherry AI Deployment Script

echo "🚀 Starting Cherry AI deployment..."

# Create directories
mkdir -p /var/www/cherry-ai/admin-interface

# Copy files
cp cherry_ai_live_collaboration_bridge.py /var/www/cherry-ai/
cp deploy_collaboration_bridge.py /var/www/cherry-ai/

# Make executable
chmod +x /var/www/cherry-ai/*.py

# Run deployment
cd /var/www/cherry-ai && python3 deploy_collaboration_bridge.py

echo "✅ Deployment initiated!"
"""
    
    return {
        "files": files_to_deploy,
        "deploy_script": deploy_script
    }

def check_server_status():
    """Check if the server is accessible"""
    try:
        response = requests.get(SERVER_URL, timeout=5)
        print(f"✅ Server is accessible: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return False

def main():
    print("🚀 Cherry AI Collaboration Bridge Uploader")
    print("="*50)
    
    # Check server
    if not check_server_status():
        print("Server is not accessible!")
        return
    
    # Create package
    package = create_deployment_package()
    
    print("\n📦 Deployment package created!")
    print(f"📡 Target server: {SERVER_IP}")
    
    # Instructions for manual deployment
    print("\n📋 Manual Deployment Instructions:")
    print("1. Access the server via console or alternative method")
    print("2. Create these files on the server:")
    
    for filename, content in package["files"].items():
        print(f"\n--- {filename} ---")
        print(f"# Save to /var/www/cherry-ai/{filename}")
        print("# (Content available in cherry_collab_deploy/ directory)")
    
    print(f"\n--- deploy.sh ---")
    print(package["deploy_script"])
    
    print("\n3. Run: chmod +x deploy.sh && ./deploy.sh")
    print("\n🔗 Once deployed, WebSocket will be available at ws://45.32.69.157:8765")

if __name__ == "__main__":
    main() 