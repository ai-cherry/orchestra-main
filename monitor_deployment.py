#!/usr/bin/env python3
"""
Orchestra AI Deployment Monitor
Real-time monitoring dashboard for all services
"""

import subprocess
import time
import json
import requests
from datetime import datetime
import os
import sys

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
CLEAR = '\033[2J\033[H'

def check_docker_service(container_name):
    """Check if a Docker container is running"""
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.State.Status}}'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "not found"

def check_port(port):
    """Check if a port is listening"""
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True, text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def check_api_health():
    """Check API health endpoint"""
    try:
        response = requests.get('http://localhost:8000/api/system/health', timeout=2)
        return response.status_code == 200, response.json()
    except:
        return False, None

def check_mcp_services():
    """Check if MCP services are running"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True
        )
        mcp_count = result.stdout.count('mcp-server')
        return mcp_count
    except:
        return 0

def get_container_logs(container_name, lines=5):
    """Get recent logs from container"""
    try:
        result = subprocess.run(
            ['docker', 'logs', container_name, '--tail', str(lines)],
            capture_output=True, text=True, stderr=subprocess.STDOUT
        )
        return result.stdout.strip()
    except:
        return "Unable to fetch logs"

def display_dashboard():
    """Display the monitoring dashboard"""
    print(CLEAR)
    print(f"{BLUE}🎼 Orchestra AI Deployment Monitor{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Docker Services
    print(f"{YELLOW}🐳 Docker Services:{RESET}")
    services = [
        ('PostgreSQL', 'cherry_ai_postgres_prod', 5432),
        ('Redis', 'cherry_ai_redis_prod', 6379),
        ('Weaviate', 'cherry_ai_weaviate_prod', 8080),
        ('API Server', 'cherry_ai_api_prod', 8000),
        ('Nginx', 'cherry_ai_nginx_prod', 80),
        ('Fluentd', 'cherry_ai_logs_prod', 24224),
        ('Monitor', 'cherry_ai_monitor_prod', None),
    ]
    
    for service_name, container_name, port in services:
        status = check_docker_service(container_name)
        if status == "running":
            status_icon = f"{GREEN}✅{RESET}"
            status_text = f"{GREEN}Running{RESET}"
        elif status == "restarting":
            status_icon = f"{YELLOW}🔄{RESET}"
            status_text = f"{YELLOW}Restarting{RESET}"
        else:
            status_icon = f"{RED}❌{RESET}"
            status_text = f"{RED}Down{RESET}"
        
        port_text = f"Port {port}" if port else "No port"
        print(f"  {status_icon} {service_name:<15} {status_text:<20} {port_text}")
    
    # API Health
    print(f"\n{YELLOW}🏥 API Health:{RESET}")
    api_healthy, api_data = check_api_health()
    if api_healthy:
        print(f"  {GREEN}✅ API is healthy{RESET}")
        if api_data:
            print(f"     Database: {api_data.get('database', 'unknown')}")
            print(f"     Status: {api_data.get('status', 'unknown')}")
    else:
        print(f"  {RED}❌ API is not responding{RESET}")
    
    # MCP Services
    print(f"\n{YELLOW}🤖 MCP Services:{RESET}")
    mcp_count = check_mcp_services()
    if mcp_count > 0:
        print(f"  {GREEN}✅ {mcp_count} MCP servers running{RESET}")
    else:
        print(f"  {RED}❌ No MCP servers detected{RESET}")
    
    # Port Status
    print(f"\n{YELLOW}🔌 Port Status:{RESET}")
    critical_ports = [
        (5432, "PostgreSQL"),
        (6379, "Redis"),
        (8080, "Weaviate"),
        (8000, "API"),
        (80, "HTTP"),
        (24224, "Fluentd")
    ]
    
    for port, service in critical_ports:
        if check_port(port):
            print(f"  {GREEN}✅{RESET} Port {port:<5} ({service})")
        else:
            print(f"  {RED}❌{RESET} Port {port:<5} ({service})")
    
    # Recent Issues
    print(f"\n{YELLOW}⚠️  Recent Issues:{RESET}")
    if check_docker_service('cherry_ai_nginx_prod') == "restarting":
        print(f"  {YELLOW}• Nginx is restarting - check configuration{RESET}")
    if check_docker_service('cherry_ai_monitor_prod') == "restarting":
        print(f"  {YELLOW}• Health monitor is restarting{RESET}")
    
    # URLs
    print(f"\n{YELLOW}🌐 Access URLs:{RESET}")
    print(f"  • API Docs: {BLUE}http://localhost:8000/docs{RESET}")
    print(f"  • API Health: {BLUE}http://localhost:8000/api/system/health{RESET}")
    print(f"  • Vercel Frontend: {BLUE}https://orchestra-admin-interface.vercel.app{RESET}")
    
    print(f"\n{BLUE}{'='*50}{RESET}")
    print("Press Ctrl+C to exit")

def main():
    """Main monitoring loop"""
    print(f"{GREEN}Starting Orchestra AI Deployment Monitor...{RESET}")
    
    try:
        while True:
            display_dashboard()
            time.sleep(5)  # Refresh every 5 seconds
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Monitoring stopped.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main() 