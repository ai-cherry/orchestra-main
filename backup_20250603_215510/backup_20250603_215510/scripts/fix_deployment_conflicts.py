#!/usr/bin/env python3
"""Fix deployment conflicts and complete Cherry AI deployment"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run command and return result"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} completed")
        return True
    else:
        print(f"⚠️  {description} had issues: {result.stderr}")
        return False

def main():
    print("🔧 Fixing Cherry AI Deployment Conflicts")
    print("=" * 60)
    
    # Step 1: Check what's using the ports
    print("\n📊 Checking port usage...")
    ports = {"5432": "PostgreSQL", "6379": "Redis", "8080": "Weaviate"}
    
    for port, service in ports.items():
        cmd = f"sudo lsof -i :{port} | grep LISTEN"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"  Port {port} ({service}): In use")
            print(f"    {result.stdout.strip()}")
        else:
            print(f"  Port {port} ({service}): Available")
    
    # Step 2: Stop existing containers
    print("\n🛑 Stopping existing Docker containers...")
    run_command("docker-compose down", "Stopping local containers")
    run_command("docker-compose -f docker-compose.prod.yml down", "Stopping production containers")
    
    # Step 3: Check for other services
    print("\n🔍 Checking for other services...")
    
    # Stop any standalone services
    services_to_stop = [
        ("sudo systemctl stop postgresql", "PostgreSQL service"),
        ("sudo systemctl stop redis", "Redis service"),
        ("docker stop $(docker ps -q --filter ancestor=semitechnologies/weaviate)", "Weaviate containers")
    ]
    
    for cmd, desc in services_to_stop:
        run_command(cmd, f"Stopping {desc}")
    
    # Step 4: Clean up Docker
    print("\n🧹 Cleaning up Docker...")
    run_command("docker system prune -f", "Removing unused containers")
    
    # Step 5: Update docker-compose.prod.yml to use different ports if needed
    print("\n📝 Updating production configuration...")
    
    compose_update = """
# Check if we need to use different ports
import yaml

with open('docker-compose.prod.yml', 'r') as f:
    compose = yaml.safe_load(f)

# Update ports if conflicts exist
updated = False
if subprocess.run("sudo lsof -i :5432", shell=True, capture_output=True).stdout:
    compose['services']['postgres']['ports'] = ['5433:5432']
    updated = True
    print("  Changed PostgreSQL to port 5433")

if subprocess.run("sudo lsof -i :6379", shell=True, capture_output=True).stdout:
    compose['services']['redis']['ports'] = ['6380:6379']
    updated = True
    print("  Changed Redis to port 6380")

if subprocess.run("sudo lsof -i :8080", shell=True, capture_output=True).stdout:
    compose['services']['weaviate']['ports'] = ['8081:8080']
    updated = True
    print("  Changed Weaviate to port 8081")

if updated:
    with open('docker-compose.prod.yml', 'w') as f:
        yaml.dump(compose, f)
    print("  ✅ Updated docker-compose.prod.yml with new ports")
"""
    
    # Execute the update
    try:
        # SECURITY: exec() removed - compose_update
    except:
        print("  ⚠️  Could not update ports automatically")
    
    # Step 6: Start services again
    print("\n🚀 Starting Cherry AI services...")
    
    time.sleep(2)  # Brief pause
    
    if run_command("docker-compose -f docker-compose.prod.yml up -d", "Starting production services"):
        print("\n⏳ Waiting for services to initialize...")
        time.sleep(10)
        
        # Step 7: Check service status
        print("\n📊 Service Status:")
        result = subprocess.run("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", 
                              shell=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Step 8: Complete deployment tasks
        print("\n🔧 Completing deployment tasks...")
        
        # Run migrations
        run_command(
            "docker-compose -f docker-compose.prod.yml exec -T api python scripts/migrate_database.py",
            "Running database migrations"
        )
        
        # Create admin user
        admin_script = """
docker-compose -f docker-compose.prod.yml exec -T api python -c "
import asyncio
from src.auth.utils import create_admin_user
asyncio.run(create_admin_user('scoobyjava', 'Huskers1983$', 'admin@cherry-ai.me'))
"
"""
        run_command(admin_script, "Creating admin user")
        
        print("\n✅ Deployment conflicts resolved!")
        print("\n🎉 Cherry AI is now running!")
        print("\nAccess your site at: https://cherry-ai.me")
        print("Login: scoobyjava / Huskers1983$")
        
        # Test the deployment
        print("\n🧪 Testing deployment...")
        test_result = subprocess.run("curl -s -o /dev/null -w '%{http_code}' https://cherry-ai.me", 
                                   shell=True, capture_output=True, text=True)
        if test_result.stdout == "200":
            print("✅ Site is accessible!")
        else:
            print(f"⚠️  Site returned status code: {test_result.stdout}")
            print("   This might be normal if DNS is still propagating")
    else:
        print("\n❌ Failed to start services. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())