#!/usr/bin/env python3
"""
"""
    """Check if a service is running."""
        return result.returncode == 0, "Running"
    except Exception:

        pass
        print(f"  Error checking {name}: {e}")
        return False, "Not running"

def main():
    """Show Cherry AI status."""
    print("\n🎼 Cherry AI System Status")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Environment
    print("\n📋 Environment")
    print("-" * 40)
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
        if path.exists():
            print(f"✓ {file} - {desc}")
        else:
            print(f"✗ {file} - {desc}")

    # MCP Servers
    print("\n🤖 MCP Servers")
    print("-" * 40)
    if mcp_file.exists():
        with open(mcp_file, "r") as f:
            mcp_config = json.load(f)

        for server_name in mcp_config.get("servers", {}).keys():
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
        "start_cherry_ai.sh": "Start script",
        "stop_cherry_ai.sh": "Stop script",
        "scripts/cherry_ai_complete_setup.py": "Setup wizard",
        "",
    }

    for script, desc in scripts.items():
        if path.exists():
            print(f"✓ {script} - {desc}")
        else:
            print(f"✗ {script} - {desc}")

    # Cleanup Status
    print("\n🧹 Cleanup Status")
    print("-" * 40)
    if not archive_dir.exists():
        print("✓ Archive directory removed")
    else:
        print("✗ Archive directory still exists")

    # Check for GCP references
    try:

        pass
        result = subprocess.run(
            ["grep", "-r", "google-cloud", "--include=*.txt", "requirements/"],
            capture_output=True,
        )
        if result.returncode == 0:
            print("✗ GCP dependencies still in requirements")
        else:
            print("✓ No GCP dependencies in requirements")
    except Exception:

        pass
        print(f"? Could not check GCP dependencies: {e}")
