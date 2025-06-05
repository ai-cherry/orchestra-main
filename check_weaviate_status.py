#!/usr/bin/env python3
"""
Check and diagnose Weaviate status on Lambda Labs
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple


def execute_ssh_command(command: str, server_ip: str = "150.136.94.139") -> Tuple[int, str, str]:
    """Execute command via SSH on Lambda Labs server."""
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no ubuntu@{server_ip} '{command}'"
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def check_weaviate_docker() -> Dict[str, any]:
    """Check if Weaviate is running in Docker."""
    print("🐳 Checking Weaviate Docker container...")
    
    # Check if container exists
    exit_code, stdout, stderr = execute_ssh_command("docker ps -a | grep weaviate")
    
    if exit_code != 0:
        print("❌ No Weaviate container found")
        return {"status": "not_found", "running": False}
    
    # Check if container is running
    exit_code, stdout, stderr = execute_ssh_command("docker ps | grep weaviate")
    
    if exit_code == 0:
        print("✅ Weaviate container is running")
        container_info = stdout.strip()
        return {"status": "running", "running": True, "info": container_info}
    else:
        print("⚠️  Weaviate container exists but is not running")
        return {"status": "stopped", "running": False}


def check_weaviate_logs() -> Optional[str]:
    """Get recent Weaviate logs."""
    print("\n📋 Fetching Weaviate logs...")
    
    exit_code, stdout, stderr = execute_ssh_command("docker logs --tail 50 weaviate 2>&1")
    
    if exit_code == 0:
        return stdout
    else:
        return None


def check_weaviate_health() -> Dict[str, any]:
    """Check Weaviate health endpoint."""
    print("\n🏥 Checking Weaviate health...")
    
    # Try different endpoints
    endpoints = [
        ("http://localhost:8080/v1/.well-known/ready", "Ready endpoint"),
        ("http://localhost:8080/v1/.well-known/live", "Live endpoint"),
        ("http://localhost:8080/v1/schema", "Schema endpoint")
    ]
    
    results = {}
    for endpoint, name in endpoints:
        exit_code, stdout, stderr = execute_ssh_command(
            f"curl -s -o /dev/null -w '%{{http_code}}' {endpoint}"
        )
        http_code = stdout.strip() if exit_code == 0 else "error"
        results[name] = http_code
        
        status = "✅" if http_code == "200" else "❌"
        print(f"  {status} {name}: {http_code}")
    
    return results


def start_weaviate() -> bool:
    """Attempt to start Weaviate container."""
    print("\n🚀 Attempting to start Weaviate...")
    
    # First, check if we need to create the container
    exit_code, stdout, stderr = execute_ssh_command("docker ps -a | grep weaviate")
    
    if exit_code != 0:
        # No container exists, create one
        print("Creating new Weaviate container...")
        
        docker_run_cmd = """docker run -d \
            --name weaviate \
            --restart unless-stopped \
            -p 8080:8080 \
            -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
            -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
            -e DEFAULT_VECTORIZER_MODULE=none \
            -e CLUSTER_HOSTNAME=node1 \
            -v /var/lib/weaviate:/var/lib/weaviate \
            semitechnologies/weaviate:latest"""
        
        exit_code, stdout, stderr = execute_ssh_command(docker_run_cmd)
        
        if exit_code == 0:
            print("✅ Weaviate container created and started")
            return True
        else:
            print(f"❌ Failed to create container: {stderr}")
            return False
    else:
        # Container exists, just start it
        exit_code, stdout, stderr = execute_ssh_command("docker start weaviate")
        
        if exit_code == 0:
            print("✅ Weaviate container started")
            return True
        else:
            print(f"❌ Failed to start container: {stderr}")
            return False


def main() -> int:
    """Main diagnostic function."""
    print("🔍 WEAVIATE DIAGNOSTIC TOOL")
    print("=" * 50)
    print(f"Target: Lambda Labs (150.136.94.139)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Docker status
    docker_status = check_weaviate_docker()
    
    # Check health endpoints
    health_status = check_weaviate_health()
    
    # Get logs if container exists
    if docker_status["status"] != "not_found":
        logs = check_weaviate_logs()
        if logs:
            print("\n📜 Recent logs (last 10 lines):")
            print("-" * 40)
            log_lines = logs.strip().split('\n')[-10:]
            for line in log_lines:
                print(f"  {line}")
    
    # Diagnosis
    print("\n🔬 DIAGNOSIS:")
    print("-" * 40)
    
    if docker_status["running"]:
        if all(code == "200" for code in health_status.values()):
            print("✅ Weaviate is running and healthy")
            return 0
        else:
            print("⚠️  Weaviate is running but not responding properly")
            print("   This might be due to:")
            print("   - Firewall blocking port 8080")
            print("   - Weaviate still initializing")
            print("   - Configuration issues")
    else:
        print("❌ Weaviate is not running")
        
        # Offer to start it
        print("\n🔧 RECOMMENDED ACTION:")
        print("   Start Weaviate with: python3 check_weaviate_status.py --start")
    
    # Save diagnostic report
    report = {
        "timestamp": datetime.now().isoformat(),
        "docker_status": docker_status,
        "health_status": health_status,
        "diagnosis": "unhealthy" if not docker_status["running"] else "degraded"
    }
    
    report_file = f"weaviate_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Diagnostic report saved to: {report_file}")
    
    # Check for --start flag
    if len(sys.argv) > 1 and sys.argv[1] == "--start":
        if not docker_status["running"]:
            if start_weaviate():
                print("\n✅ Weaviate started successfully!")
                print("   Wait 30 seconds for it to fully initialize")
                return 0
            else:
                print("\n❌ Failed to start Weaviate")
                return 1
    
    return 1 if not docker_status["running"] else 0


if __name__ == "__main__":
    sys.exit(main())