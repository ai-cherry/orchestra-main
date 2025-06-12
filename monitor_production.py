#!/usr/bin/env python3
import time
import subprocess
import json
import requests
from datetime import datetime

def get_service_status():
    """Get status of all services"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "docker": check_docker_services(),
            "api": check_api_health(),
            "mcp": check_mcp_servers(),
            "pulumi": check_pulumi_resources()
        }
    }
    return status

def check_docker_services():
    """Check Docker container status"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        containers = result.stdout.strip().split('\n')
        return {
            "status": "healthy",
            "count": len(containers),
            "containers": containers
        }
    except:
        return {"status": "error", "count": 0}

def check_api_health():
    """Check API health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/system/health", timeout=2)
        if response.status_code == 200:
            return {"status": "healthy", "data": response.json()}
        else:
            return {"status": "error", "code": response.status_code}
    except:
        return {"status": "error", "message": "Connection failed"}

def check_mcp_servers():
    """Check MCP server processes"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        mcp_count = len([line for line in result.stdout.split('\n') if 'mcp' in line.lower() and 'grep' not in line])
        return {"status": "healthy", "count": mcp_count}
    except:
        return {"status": "error", "count": 0}

def check_pulumi_resources():
    """Check Pulumi stack resources"""
    try:
        result = subprocess.run(
            ["pulumi", "stack", "--json"],
            capture_output=True,
            text=True,
            cwd="infrastructure/pulumi"
        )
        data = json.loads(result.stdout)
        return {
            "status": "healthy",
            "resources": data.get("summary", {}).get("resourceCount", 0)
        }
    except:
        return {"status": "unknown", "resources": 0}

# Main monitoring loop
print("🎼 Orchestra AI Production Monitor Started")
print("=====================================")

while True:
    status = get_service_status()
    
    # Display status
    print(f"\n📅 {status['timestamp']}")
    print(f"Docker: {status['services']['docker']['status']} ({status['services']['docker']['count']} containers)")
    print(f"API: {status['services']['api']['status']}")
    print(f"MCP: {status['services']['mcp']['status']} ({status['services']['mcp']['count']} servers)")
    print(f"Pulumi: {status['services']['pulumi']['resources']} resources")
    
    # Write to log file
    with open("production_status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    time.sleep(30)  # Check every 30 seconds
