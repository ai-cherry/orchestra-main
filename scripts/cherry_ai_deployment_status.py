#!/usr/bin/env python3
"""Cherry AI Website Deployment Status - Complete verification of cherry-ai.me deployment"""

import os
import sys
import subprocess
import requests
import json
from datetime import datetime
from pathlib import Path

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(title):
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def check_status(description, condition, details=""):
    """Print status check result"""
    if condition:
        print(f"  {GREEN}✓{RESET} {description}")
        if details:
            print(f"    {details}")
    else:
        print(f"  {RED}✗{RESET} {description}")
        if details:
            print(f"    {details}")
    return condition

def main():
    """Main status check function"""
    print(f"{BOLD}{BLUE}Cherry AI Website Deployment Status{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Domain: https://cherry-ai.me")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    all_good = True
    
    # 1. Infrastructure Status
    print_header("Infrastructure Status")
    
    # Check Docker services
    services = {
        "PostgreSQL": "orchestra-main_postgres_1",
        "Redis": "orchestra-main_redis_1",
        "Weaviate": "orchestra-main_weaviate_1",
        "API": "orchestra-main_api_1"
    }
    
    for name, container in services.items():
        try:
            result = subprocess.run(
                f"docker inspect {container} --format '{{{{.State.Status}}}}'",
                shell=True, capture_output=True, text=True
            )
            status = result.stdout.strip()
            all_good &= check_status(f"{name} Container", status == "running", f"Status: {status}")
        except:
            all_good &= check_status(f"{name} Container", False, "Not found")
    
    # Check Nginx
    try:
        result = subprocess.run("systemctl is-active nginx", shell=True, capture_output=True, text=True)
        nginx_active = result.stdout.strip() == "active"
        all_good &= check_status("Nginx", nginx_active, f"Status: {result.stdout.strip()}")
    except:
        all_good &= check_status("Nginx", False, "Unable to check")
    
    # 2. API Endpoints
    print_header("API Endpoints")
    
    endpoints = [
        ("Health Check", "https://cherry-ai.me/health"),
        ("API Health (compatibility)", "https://cherry-ai.me/api/health"),
        ("API Docs", "https://cherry-ai.me/docs"),
        ("OpenAPI Schema", "https://cherry-ai.me/openapi.json"),
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5, verify=True)
            success = response.status_code == 200
            all_good &= check_status(name, success, f"Status: {response.status_code}")
            
            if success and "health" in url:
                data = response.json()
                print(f"    Response: {json.dumps(data, indent=2)}")
        except requests.exceptions.SSLError:
            all_good &= check_status(name, False, "SSL Error")
        except Exception as e:
            all_good &= check_status(name, False, f"Error: {type(e).__name__}")
    
    # 3. Website Accessibility
    print_header("Website Accessibility")
    
    pages = [
        ("Homepage", "https://cherry-ai.me/"),
        ("Admin Panel", "https://cherry-ai.me/admin/"),
    ]
    
    for name, url in pages:
        try:
            response = requests.get(url, timeout=10, verify=True)
            success = response.status_code == 200
            all_good &= check_status(name, success, f"Status: {response.status_code}")
            
            if success:
                content_length = len(response.content)
                print(f"    Content size: {content_length:,} bytes")
        except Exception as e:
            all_good &= check_status(name, False, f"Error: {type(e).__name__}")
    
    # 4. SSL Certificate
    print_header("SSL Certificate")
    
    cert_path = "/etc/letsencrypt/live/cherry-ai.me/fullchain.pem"
    if Path(cert_path).exists():
        try:
            result = subprocess.run(
                f"openssl x509 -enddate -noout -in {cert_path}",
                shell=True, capture_output=True, text=True
            )
            check_status("SSL Certificate", True, result.stdout.strip())
            
            # Check days until expiry
            result = subprocess.run(
                f"openssl x509 -checkend 2592000 -noout -in {cert_path}",
                shell=True, capture_output=True
            )
            if result.returncode == 0:
                print(f"    {GREEN}Certificate valid for 30+ days{RESET}")
            else:
                print(f"    {YELLOW}Certificate expires within 30 days!{RESET}")
        except:
            check_status("SSL Certificate", False, "Unable to check")
    else:
        all_good &= check_status("SSL Certificate", False, "Not found")
    
    # 5. Database Status
    print_header("Database Status")
    
    try:
        # Check if we can connect to PostgreSQL
        result = subprocess.run(
            "docker exec orchestra-main_postgres_1 pg_isready -U postgres",
            shell=True, capture_output=True, text=True
        )
        db_ready = "accepting connections" in result.stdout
        check_status("PostgreSQL Connection", db_ready, result.stdout.strip())
        
        # Check database size
        result = subprocess.run(
            "docker exec orchestra-main_postgres_1 psql -U postgres -d cherry_ai -t -c \"SELECT pg_size_pretty(pg_database_size('cherry_ai'));\"",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"    Database size: {result.stdout.strip()}")
    except:
        all_good &= check_status("PostgreSQL Connection", False, "Unable to check")
    
    # 6. Redis Status
    print_header("Redis Status")
    
    try:
        result = subprocess.run(
            "docker exec orchestra-main_redis_1 redis-cli ping",
            shell=True, capture_output=True, text=True
        )
        redis_ok = result.stdout.strip() == "PONG"
        check_status("Redis Connection", redis_ok)
        
        # Get Redis info
        result = subprocess.run(
            "docker exec orchestra-main_redis_1 redis-cli INFO server | grep redis_version",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"    {result.stdout.strip()}")
    except:
        all_good &= check_status("Redis Connection", False, "Unable to check")
    
    # Summary
    print_header("Deployment Summary")
    
    if all_good:
        print(f"{GREEN}✅ Cherry AI website is fully deployed and operational!{RESET}\n")
        print(f"Access Points:")
        print(f"  🌐 Website: https://cherry-ai.me")
        print(f"  👤 Admin: https://cherry-ai.me/admin")
        print(f"  📚 API Docs: https://cherry-ai.me/docs")
        print(f"  🔧 API Schema: https://cherry-ai.me/openapi.json")
        print(f"\nCredentials:")
        print(f"  Username: scoobyjava")
        print(f"  Password: Huskers1983$")
    else:
        print(f"{RED}❌ Some issues detected with the deployment{RESET}\n")
        print(f"Please check the failed items above and:")
        print(f"  1. Ensure all Docker containers are running")
        print(f"  2. Check Nginx configuration and logs")
        print(f"  3. Verify SSL certificate is valid")
        print(f"  4. Check application logs for errors")
    
    print(f"\n{BOLD}Useful Commands:{RESET}")
    print(f"  View logs: docker-compose -f docker-compose.single-user.yml logs -f")
    print(f"  Restart services: docker-compose -f docker-compose.single-user.yml restart")
    print(f"  Check Nginx: sudo nginx -t && sudo systemctl status nginx")
    print(f"  Monitor Redis: python3 scripts/redis_health_monitor.py monitor")

if __name__ == "__main__":
    main()