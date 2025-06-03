#!/usr/bin/env python3
"""Orchestra System Status Checker"""

import subprocess
import json
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path


def check_service(service_name: str) -> Tuple[bool, str]:
    """Check if a service is running."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0, "Running" if result.returncode == 0 else "Stopped"
    except Exception as e:
        return False, str(e)


def get_docker_containers() -> List[str]:
    """Get list of running Docker containers."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout else []
        return []
    except Exception:
        return []


def check_postgres() -> Dict[str, any]:
    """Check PostgreSQL status"""
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True,
            text=True
        )
        return {
            "status": "healthy" if result.returncode == 0 else "unhealthy",
            "message": result.stdout.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_redis() -> Dict[str, any]:
    """Check Redis status"""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True
        )
        return {
            "status": "healthy" if result.stdout.strip() == "PONG" else "unhealthy",
            "message": result.stdout.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_weaviate() -> Dict[str, any]:
    """Check Weaviate status"""
    try:
        import requests
        response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=5)
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "message": f"HTTP {response.status_code}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """Main status check function"""
    print("🔍 Orchestra AI System Status Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Check Docker containers
    print("\n📦 Docker Containers:")
    containers = get_docker_containers()
    if containers:
        for container in containers:
            print(f"  ✅ {container}")
    else:
        print("  ❌ No containers running")
    
    # Check services
    print("\n🔧 Services:")
    services = {
        "PostgreSQL": check_postgres(),
        "Redis": check_redis(),
        "Weaviate": check_weaviate()
    }
    
    for service, status in services.items():
        icon = "✅" if status["status"] == "healthy" else "❌"
        print(f"  {icon} {service}: {status['status']} - {status['message']}")
    
    # Overall status
    all_healthy = all(s["status"] == "healthy" for s in services.values())
    overall_status = "✅ All systems operational" if all_healthy else "⚠️ Some services need attention"
    
    print(f"\n{overall_status}")
    
    # Export status as JSON
    status_data = {
        "timestamp": datetime.now().isoformat(),
        "containers": containers,
        "services": services,
        "overall_healthy": all_healthy
    }
    
    status_file = Path("orchestra_status.json")
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)
    
    print(f"\n📄 Status exported to: {status_file}")


if __name__ == "__main__":
    main()
