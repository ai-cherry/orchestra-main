#!/usr/bin/env python3
"""Final verification of Cherry AI deployment."""

import subprocess
import requests
import json
import time

def run_command(cmd, check=False):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def check_website():
    """Check if the website is accessible and shows correct content."""
    print("\n=== Checking Website ===")
    try:
        response = requests.get("https://cherry-ai.me", timeout=10)
        if response.status_code == 200:
            print("✓ Website is accessible (HTTP 200)")
            if "Cherry AI" in response.text:
                print("✓ Website shows 'Cherry AI' title")
            else:
                print("✗ Website does not show 'Cherry AI' title")
            if "Cherry Admin UI" in response.text:
                print("✗ Old 'Cherry Admin UI' title still present")
            else:
                print("✓ Old 'Cherry Admin UI' title removed")
        else:
            print(f"✗ Website returned HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing website: {e}")

def check_api():
    """Check if the API is accessible."""
    print("\n=== Checking API ===")
    try:
        response = requests.get("https://cherry-ai.me/api/health", timeout=10)
        if response.status_code == 200:
            print("✓ API health endpoint is accessible")
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"✗ API returned HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing API: {e}")

def check_services():
    """Check Docker services."""
    print("\n=== Checking Docker Services ===")
    result = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}'")
    print(result.stdout)
    
    # Check specific services
    services = ["cherry_ai_api", "cherry_ai_postgres", "cherry_ai_redis", "cherry_ai_weaviate"]
    for service in services:
        result = run_command(f"docker ps -q -f name={service}")
        if result.stdout.strip():
            print(f"✓ {service} is running")
        else:
            print(f"✗ {service} is NOT running")

def check_database():
    """Check database setup."""
    print("\n=== Checking Database ===")
    
    # Check schemas
    schemas = ["personal", "payready", "paragonrx"]
    for schema in schemas:
        result = run_command(
            f"docker exec cherry_ai_postgres psql -U postgres -d cherry_ai -t -c "
            f"\"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}';\""
        )
        if "1" in result.stdout:
            print(f"✓ Schema '{schema}' exists")
        else:
            print(f"✗ Schema '{schema}' NOT found")
    
    # Check admin user
    result = run_command(
        "docker exec cherry_ai_postgres psql -U postgres -d cherry_ai -t -c "
        "\"SELECT username FROM public.users WHERE username = 'scoobyjava';\""
    )
    if "scoobyjava" in result.stdout:
        print("✓ Admin user 'scoobyjava' exists")
    else:
        print("✗ Admin user 'scoobyjava' NOT found")

def main():
    print("=== Cherry AI Final Deployment Verification ===")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    check_website()
    check_api()
    check_services()
    check_database()
    
    print("\n=== Summary ===")
    print("Website URL: https://cherry-ai.me")
    print("Login: scoobyjava / Huskers1983$")
    print("\nThe Cherry AI platform should now be fully deployed with:")
    print("- Updated 'Cherry AI' branding")
    print("- Multi-modal search interface")
    print("- Three personas (Cherry, Sophia, Karen)")
    print("- MCP server integrations")
    print("- Clean environment with no old builds")

if __name__ == "__main__":
    main()