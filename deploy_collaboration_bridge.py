#!/usr/bin/env python3
"""
Deploy Cherry AI Live Collaboration Bridge
This script sets up and runs the WebSocket collaboration server
"""

import os
import sys
import subprocess
import asyncio

def setup_environment():
    """Set up the Python environment and install dependencies"""
    print("🔧 Setting up environment...")
    
    # Update package list
    subprocess.run(["apt-get", "update", "-y"], check=False)
    
    # Install Python and pip if needed
    subprocess.run(["apt-get", "install", "-y", "python3", "python3-pip"], check=False)
    
    # Install required Python packages
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "asyncio"], check=True)
    
    print("✅ Environment setup complete!")

def create_systemd_service():
    """Create a systemd service for the collaboration bridge"""
    service_content = """[Unit]
Description=Cherry AI Live Collaboration Bridge
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/cherry-ai
ExecStart=/usr/bin/python3 /var/www/cherry-ai/cherry_ai_live_collaboration_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/cherry-collab.service", "w") as f:
        f.write(service_content)
    
    # Reload systemd and enable service
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "cherry-collab.service"], check=True)
    subprocess.run(["systemctl", "start", "cherry-collab.service"], check=True)
    
    print("✅ Systemd service created and started!")

def check_firewall():
    """Ensure port 8765 is open for WebSocket connections"""
    print("🔥 Configuring firewall...")
    
    # Check if ufw is installed
    try:
        subprocess.run(["ufw", "allow", "8765/tcp"], check=True)
        subprocess.run(["ufw", "allow", "22/tcp"], check=True)  # SSH
        subprocess.run(["ufw", "allow", "80/tcp"], check=True)   # HTTP
        subprocess.run(["ufw", "allow", "443/tcp"], check=True)  # HTTPS
        print("✅ Firewall rules updated!")
    except:
        print("⚠️  UFW not found, checking iptables...")
        # Add iptables rule as fallback
        subprocess.run([
            "iptables", "-A", "INPUT", "-p", "tcp", "--dport", "8765", "-j", "ACCEPT"
        ], check=False)

def deploy_cherry_ai_interface():
    """Deploy the enhanced Cherry AI interface"""
    print("🚀 Deploying Cherry AI interface...")
    
    # Create directories if they don't exist
    os.makedirs("/var/www/html", exist_ok=True)
    os.makedirs("/var/www/cherry-ai/admin-interface", exist_ok=True)
    
    # Create the enhanced interface if it doesn't exist
    enhanced_interface = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherry AI - Live Collaboration Active</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 2rem;
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .status {
            background: rgba(255,255,255,0.2);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .personas {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 2rem;
        }
        .persona {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 15px;
            width: 200px;
        }
        .persona h3 {
            margin: 0 0 0.5rem 0;
        }
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff00;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌸 Cherry AI</h1>
        <div class="status">
            <p><span class="live-indicator"></span> Live Collaboration Active</p>
            <p>WebSocket Server: 45.32.69.157:8765</p>
        </div>
        
        <h2>AI Personas</h2>
        <div class="personas">
            <div class="persona">
                <h3>🌸 Cherry</h3>
                <p>Personal AI Assistant</p>
            </div>
            <div class="persona">
                <h3>💼 Sophia</h3>
                <p>Business Strategy AI</p>
            </div>
            <div class="persona">
                <h3>🏥 Karen</h3>
                <p>Healthcare AI Specialist</p>
            </div>
        </div>
        
        <p style="margin-top: 2rem; opacity: 0.8;">
            Manus + Cursor AI Collaboration Bridge Active
        </p>
    </div>
</body>
</html>"""
    
    # Write the enhanced interface
    with open("/var/www/html/index.html", "w") as f:
        f.write(enhanced_interface)
    
    # Also save to admin-interface directory
    with open("/var/www/cherry-ai/admin-interface/enhanced-production-interface.html", "w") as f:
        f.write(enhanced_interface)
    
    print("✅ Cherry AI interface deployed!")

def main():
    print("🚀 Cherry AI Collaboration Bridge Deployment Script")
    print("="*50)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root!")
        sys.exit(1)
    
    try:
        # Step 1: Setup environment
        setup_environment()
        
        # Step 2: Deploy interface
        deploy_cherry_ai_interface()
        
        # Step 3: Configure firewall
        check_firewall()
        
        # Step 4: Create and start service
        create_systemd_service()
        
        print("\n✅ Deployment complete!")
        print("📡 WebSocket server running on port 8765")
        print("🌐 Cherry AI interface available at http://45.32.69.157")
        print("\n📋 Check status with: systemctl status cherry-collab")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 