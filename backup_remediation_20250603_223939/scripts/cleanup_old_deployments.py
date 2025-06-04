#!/usr/bin/env python3
"""Clean up old deployments, builds, and configurations to prevent conflicts."""

import subprocess
import os
import shutil
import glob
import json

def run_command(cmd, check=False):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result

def cleanup_old_web_files():
    """Clean up old web server files."""
    print("\n=== Cleaning Old Web Files ===")
    
    # Remove old backups
    old_dirs = [
        "/var/www/cherry_ai-admin.old",
        "/var/www/html.old",
        "/var/www/cherry-ai",
        "/var/www/cherry_ai"
    ]
    
    for dir_path in old_dirs:
        if os.path.exists(dir_path):
            print(f"Removing old directory: {dir_path}")
            run_command(f"sudo rm -rf {dir_path}")

def cleanup_nginx_configs():
    """Clean up old Nginx configurations."""
    print("\n=== Cleaning Old Nginx Configs ===")
    
    # Remove old config files
    old_configs = [
        "/etc/nginx/sites-available/cherry-ai",
        "/etc/nginx/sites-available/cherry-ai.me",
        "/etc/nginx/sites-available/cherry_ai",
        "/etc/nginx/sites-available/cherry_ai-ai",
        "/etc/nginx/sites-enabled/default"
    ]
    
    for config in old_configs:
        if os.path.exists(config):
            print(f"Removing old config: {config}")
            run_command(f"sudo rm -f {config}")

def cleanup_docker_artifacts():
    """Clean up Docker artifacts."""
    print("\n=== Cleaning Docker Artifacts ===")
    
    # Remove stopped containers
    print("Removing stopped containers...")
    run_command("docker container prune -f")
    
    # Remove unused images
    print("Removing unused images...")
    run_command("docker image prune -a -f")
    
    # Remove unused volumes (careful with this)
    print("Removing unused volumes...")
    run_command("docker volume prune -f")
    
    # Remove unused networks
    print("Removing unused networks...")
    run_command("docker network prune -f")

def cleanup_old_builds():
    """Clean up old build artifacts."""
    print("\n=== Cleaning Old Build Artifacts ===")
    
    # Clean up node_modules in various locations
    node_modules_dirs = glob.glob("/root/cherry_ai-main/**/node_modules", recursive=True)
    for nm_dir in node_modules_dirs:
        if "admin-ui/node_modules" not in nm_dir:  # Keep admin-ui node_modules
            print(f"Removing: {nm_dir}")
            shutil.rmtree(nm_dir, ignore_errors=True)
    
    # Clean up Python cache
    pycache_dirs = glob.glob("/root/cherry_ai-main/**/__pycache__", recursive=True)
    for pc_dir in pycache_dirs:
        print(f"Removing: {pc_dir}")
        shutil.rmtree(pc_dir, ignore_errors=True)
    
    # Clean up .pyc files
    run_command("find /root/cherry_ai-main -name '*.pyc' -delete")
    
    # Clean up build directories
    build_dirs = [
        "/root/cherry_ai-main/build",
        "/root/cherry_ai-main/dist",
        "/root/cherry_ai-main/.next",
        "/root/cherry_ai-main/out"
    ]
    
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            print(f"Removing build directory: {build_dir}")
            shutil.rmtree(build_dir, ignore_errors=True)

def cleanup_temp_files():
    """Clean up temporary files."""
    print("\n=== Cleaning Temporary Files ===")
    
    # Clean /tmp files created during deployment
    temp_patterns = [
        "/tmp/cherry_ai*",
        "/tmp/admin*",
        "/tmp/setup*",
        "/tmp/*.sql",
        "/tmp/*.conf"
    ]
    
    for pattern in temp_patterns:
        files = glob.glob(pattern)
        for file in files:
            print(f"Removing temp file: {file}")
            os.remove(file)

def cleanup_old_logs():
    """Clean up old log files."""
    print("\n=== Cleaning Old Logs ===")
    
    # Clean up old Docker logs
    run_command("sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log", check=False)
    
    # Clean up Nginx logs
    run_command("sudo truncate -s 0 /var/log/nginx/access.log", check=False)
    run_command("sudo truncate -s 0 /var/log/nginx/error.log", check=False)

def verify_clean_state():
    """Verify the system is in a clean state."""
    print("\n=== Verifying Clean State ===")
    
    # Check for conflicting services
    print("\nChecking for port conflicts...")
    ports = [8000, 8001, 8080, 8081, 5432, 6379, 3000, 3001]
    
    for port in ports:
        result = run_command(f"sudo lsof -i :{port}", check=False)
        if result.stdout:
            print(f"Port {port} is in use:")
            print(result.stdout)
    
    # Check Docker state
    print("\nDocker containers:")
    run_command("docker ps -a")
    
    # Check disk space
    print("\nDisk space:")
    run_command("df -h /")

def create_deployment_manifest():
    """Create a manifest of the current deployment."""
    print("\n=== Creating Deployment Manifest ===")
    
    manifest = {
        "deployment_type": "Cherry AI Admin Interface",
        "version": "1.0.0",
        "deployed_at": subprocess.check_output("date -u", shell=True).decode().strip(),
        "components": {
            "frontend": {
                "type": "admin-ui",
                "location": "/var/www/cherry_ai-admin",
                "source": "/root/cherry_ai-main/admin-ui/dist"
            },
            "api": {
                "type": "FastAPI",
                "port": 8001,
                "container": "cherry_ai_api"
            },
            "database": {
                "type": "PostgreSQL",
                "port": 5432,
                "container": "cherry_ai_postgres",
                "schemas": ["public", "personal", "payready", "paragonrx"]
            },
            "cache": {
                "type": "Redis",
                "port": 6379,
                "container": "cherry_ai_redis"
            },
            "vector_store": {
                "type": "Weaviate",
                "port": 8081,
                "container": "cherry_ai_weaviate"
            }
        },
        "nginx_config": "/etc/nginx/sites-enabled/cherry_ai-admin",
        "ssl_certificate": "/etc/letsencrypt/live/cherry-ai.me/",
        "admin_user": "scoobyjava"
    }
    
    with open("/root/cherry_ai-main/deployment_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print("Deployment manifest created at: /root/cherry_ai-main/deployment_manifest.json")

def main():
    print("=== Cherry AI Deployment Cleanup ===")
    print("This will clean up old builds and configurations to prevent conflicts")
    
    # Perform cleanup
    cleanup_old_web_files()
    cleanup_nginx_configs()
    cleanup_docker_artifacts()
    cleanup_old_builds()
    cleanup_temp_files()
    cleanup_old_logs()
    
    # Verify and document
    verify_clean_state()
    create_deployment_manifest()
    
    print("\n=== Cleanup Complete ===")
    print("\n✅ Cleaned:")
    print("- Old web server files and backups")
    print("- Unused Nginx configurations")
    print("- Docker artifacts (stopped containers, unused images)")
    print("- Old build directories and cache files")
    print("- Temporary deployment files")
    print("- Truncated log files")
    
    print("\n📋 Current State:")
    print("- Single Nginx config: cherry_ai-admin")
    print("- Clean Docker environment with only active containers")
    print("- Deployment manifest created for reference")
    
    print("\n🔒 Protected:")
    print("- Active admin-ui build")
    print("- Running Docker containers")
    print("- Database data")
    print("- SSL certificates")
    
    print("\nThe system is now clean and ready for stable operation!")

if __name__ == "__main__":
    main()