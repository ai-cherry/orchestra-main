#!/usr/bin/env python3
"""
Orchestra AI Status - Show complete system status
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def check_service(name: str, command: list) -> tuple:
    """Check if a service is running."""
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.returncode == 0, "Running"
    except Exception as e:
        print(f"  Error checking {name}: {e}")
        return False, "Not running"


def main():
    """Show Orchestra AI status."""
    root_dir = Path(__file__).parent.parent

    print("\n🎼 Orchestra AI System Status")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Environment
    print("\n📋 Environment")
    print("-" * 40)
    env_file = root_dir / ".env"
    if env_file.exists():
        print("✓ .env file configured")
        # Count configured services
        with open(env_file, "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#") and "=" in l]
        print(f"  {len(lines)} environment variables set")
    else:
        print("✗ .env file missing")

    # Configuration Files
    print("\n📁 Configuration Files")
    print("-" * 40)
    configs = {
        ".mcp.json": "MCP configuration",
        "docker-compose.yml": "Docker Compose",
        "ARCHITECTURE_CONTEXT.md": "Architecture docs",
        ".ai-context-index.md": "AI context index",
    }

    for file, desc in configs.items():
        path = root_dir / file
        if path.exists():
            print(f"✓ {file} - {desc}")
        else:
            print(f"✗ {file} - {desc}")

    # MCP Servers
    print("\n🤖 MCP Servers")
    print("-" * 40)
    mcp_file = root_dir / ".mcp.json"
    if mcp_file.exists():
        with open(mcp_file, "r") as f:
            mcp_config = json.load(f)

        for server_name in mcp_config.get("servers", {}).keys():
            server_file = root_dir / "mcp_server" / "servers" / f"{server_name}_server.py"
            if server_file.exists():
                print(f"✓ {server_name} server - Ready")
            else:
                print(f"✗ {server_name} server - Missing")

    # Services
    print("\n🔧 Services")
    print("-" * 40)

    # Check Docker
    docker_running, docker_status = check_service("Docker", ["docker", "ps"])
    print(f"{'✓' if docker_running else '✗'} Docker - {docker_status}")

    # Check Redis
    redis_running, redis_status = check_service("Redis", ["redis-cli", "ping"])
    print(f"{'✓' if redis_running else '✗'} Redis - {redis_status}")

    # Automation Scripts
    print("\n🚀 Automation")
    print("-" * 40)
    scripts = {
        "start_orchestra.sh": "Start script",
        "stop_orchestra.sh": "Stop script",
        "scripts/orchestra_complete_setup.py": "Setup wizard",
        "scripts/test_new_setup.py": "Test suite",
    }

    for script, desc in scripts.items():
        path = root_dir / script
        if path.exists():
            print(f"✓ {script} - {desc}")
        else:
            print(f"✗ {script} - {desc}")

    # Cleanup Status
    print("\n🧹 Cleanup Status")
    print("-" * 40)
    archive_dir = root_dir / "scripts" / "archive"
    if not archive_dir.exists():
        print("✓ Archive directory removed")
    else:
        print("✗ Archive directory still exists")

    # Check for GCP references
    try:
        result = subprocess.run(
            ["grep", "-r", "google-cloud", "--include=*.txt", "requirements/"],
            capture_output=True,
            cwd=root_dir,
        )
        if result.returncode == 0:
            print("✗ GCP dependencies still in requirements")
        else:
            print("✓ No GCP dependencies in requirements")
    except Exception as e:
        print(f"? Could not check GCP dependencies: {e}")
