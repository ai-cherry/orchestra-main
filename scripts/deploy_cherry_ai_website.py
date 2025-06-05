#!/usr/bin/env python3
"""
Cherry AI Website Deployment and Verification Script
Ensures cherry-ai.me is properly set up, configured, and deployed
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class CherryAIDeployment:
    """Orchestrates Cherry AI website deployment"""
    
    def __init__(self):
        self.domain = "cherry-ai.me"
        self.api_port = 8001
        self.frontend_port = 3000
        self.deployment_steps = []
        self.issues = []
        
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{title:^60}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def run_command(self, cmd: str, description: str, check=True) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        print(f"{description}...", end='', flush=True)
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            if result.returncode == 0:
                print(f" {GREEN}✓{RESET}")
                return True, result.stdout
            else:
                print(f" {RED}✗{RESET}")
                self.issues.append(f"{description}: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            print(f" {RED}✗{RESET}")
            self.issues.append(f"{description}: {str(e)}")
            return False, str(e)
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        self.print_header("Checking Prerequisites")
        
        checks = [
            ("Docker", "docker --version"),
            ("Docker Compose", "docker-compose --version"),
            ("Git", "git --version"),
            ("Python 3", "python3 --version"),
            ("Nginx", "nginx -v 2>&1"),
            ("Curl", "curl --version | head -1"),
        ]
        
        all_good = True
        for name, cmd in checks:
            success, _ = self.run_command(cmd, f"Checking {name}", check=False)
            if not success:
                all_good = False
        
        return all_good
    
    def check_docker_services(self):
        """Check Docker services status"""
        self.print_header("Checking Docker Services")
        
        services = [
            ("PostgreSQL", "orchestra-main_postgres_1"),
            ("Redis", "orchestra-main_redis_1"),
            ("Weaviate", "orchestra-main_weaviate_1"),
            ("API", "orchestra-main_api_1"),
        ]
        
        all_running = True
        for name, container in services:
            cmd = f"docker ps --filter name={container} --format '{{{{.Status}}}}'"
            success, output = self.run_command(cmd, f"Checking {name}")
            if not success or not output.strip():
                all_running = False
        
        return all_running
    
    def check_api_health(self):
        """Check API health endpoints"""
        self.print_header("Checking API Health")
        
        endpoints = [
            ("API Health", f"http://localhost:{self.api_port}/health"),
            ("API Docs", f"http://localhost:{self.api_port}/docs"),
            ("Database Connection", f"http://localhost:{self.api_port}/api/health/db"),
        ]
        
        all_healthy = True
        for name, url in endpoints:
            try:
                print(f"Checking {name}...", end='', flush=True)
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f" {GREEN}✓{RESET} (Status: {response.status_code})")
                else:
                    print(f" {YELLOW}⚠{RESET} (Status: {response.status_code})")
                    all_healthy = False
            except Exception as e:
                print(f" {RED}✗{RESET} ({str(e)})")
                all_healthy = False
                self.issues.append(f"{name}: {str(e)}")
        
        return all_healthy
    
    def check_nginx_config(self):
        """Check and validate Nginx configuration"""
        self.print_header("Checking Nginx Configuration")
        
        # Test nginx config
        success, _ = self.run_command("nginx -t", "Testing Nginx configuration")
        if not success:
            return False
        
        # Check if cherry-ai.me is configured
        nginx_sites = [
            "/etc/nginx/sites-enabled/cherry-ai.me",
            "/etc/nginx/sites-available/cherry-ai.me",
            "/etc/nginx/conf.d/cherry-ai.me.conf"
        ]
        
        config_found = False
        for site in nginx_sites:
            if Path(site).exists():
                print(f"  {GREEN}✓{RESET} Found config at {site}")
                config_found = True
                break
        
        if not config_found:
            print(f"  {YELLOW}⚠{RESET} No cherry-ai.me nginx config found")
            self.issues.append("Nginx configuration for cherry-ai.me not found")
        
        return config_found
    
    def check_ssl_certificate(self):
        """Check SSL certificate status"""
        self.print_header("Checking SSL Certificate")
        
        cert_path = "/etc/letsencrypt/live/cherry-ai.me/fullchain.pem"
        if Path(cert_path).exists():
            print(f"  {GREEN}✓{RESET} SSL certificate found")
            
            # Check certificate expiry
            cmd = f"openssl x509 -enddate -noout -in {cert_path}"
            success, output = self.run_command(cmd, "Checking certificate expiry")
            if success:
                print(f"  Certificate info: {output.strip()}")
            return True
        else:
            print(f"  {RED}✗{RESET} SSL certificate not found")
            self.issues.append("SSL certificate not found - need to run certbot")
            return False
    
    def check_website_accessibility(self):
        """Check if website is accessible"""
        self.print_header("Checking Website Accessibility")
        
        urls = [
            (f"https://{self.domain}", "Main website"),
            (f"https://{self.domain}/api/health", "API endpoint"),
            (f"https://{self.domain}/admin", "Admin panel"),
        ]
        
        all_accessible = True
        for url, description in urls:
            try:
                print(f"Checking {description}...", end='', flush=True)
                response = requests.get(url, timeout=10, verify=True)
                if response.status_code == 200:
                    print(f" {GREEN}✓{RESET} (Status: {response.status_code})")
                else:
                    print(f" {YELLOW}⚠{RESET} (Status: {response.status_code})")
                    if response.status_code == 502:
                        self.issues.append(f"{description}: Backend service not running")
                    elif response.status_code == 404:
                        self.issues.append(f"{description}: Route not configured")
            except requests.exceptions.SSLError:
                print(f" {RED}✗{RESET} (SSL Error)")
                self.issues.append(f"{description}: SSL certificate issue")
                all_accessible = False
            except requests.exceptions.ConnectionError:
                print(f" {RED}✗{RESET} (Connection Error)")
                self.issues.append(f"{description}: Site not reachable")
                all_accessible = False
            except Exception as e:
                print(f" {RED}✗{RESET} ({type(e).__name__})")
                self.issues.append(f"{description}: {str(e)}")
                all_accessible = False
        
        return all_accessible
    
    def deploy_services(self):
        """Deploy or restart services"""
        self.print_header("Deploying Services")
        
        # Start Docker services
        print("\n1. Starting Docker services...")
        success, _ = self.run_command(
            "docker-compose -f docker-compose.single-user.yml up -d",
            "Starting Docker containers"
        )
        
        if success:
            print("   Waiting for services to be ready...")
            # TODO: Replace with asyncio.sleep() for async code
            time.sleep(10)
        
        # Run database migrations
        print("\n2. Running database migrations...")
        self.run_command(
            "docker exec orchestra-main_api_1 python -m alembic upgrade head",
            "Running Alembic migrations",
            check=False
        )
        
        # Restart Nginx
        print("\n3. Restarting Nginx...")
        self.run_command("sudo systemctl restart nginx", "Restarting Nginx")
        
        return success
    
    def create_nginx_config(self):
        """Create Nginx configuration for cherry-ai.me"""
        self.print_header("Creating Nginx Configuration")
        
        nginx_config = """server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cherry-ai.me www.cherry-ai.me;
    
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://cherry-ai.me" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        add_header Access-Control-Allow-Credentials "true" always;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Frontend (static files or reverse proxy)
    location / {
        # If using static files
        root /var/www/cherry-ai.me;
        try_files $uri $uri/ /index.html;
        
        # If using reverse proxy to frontend dev server
        # proxy_pass http://localhost:3000;
        # proxy_set_header Host $host;
        # proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Admin panel
    location /admin {
        alias /var/www/cherry-ai.me/admin;
        try_files $uri $uri/ /admin/index.html;
    }
}"""
        
        config_path = "/tmp/cherry-ai.me.nginx"
        with open(config_path, 'w') as f:
            f.write(nginx_config)
        
        print(f"Created Nginx config at {config_path}")
        print("\nTo install:")
        print(f"  sudo cp {config_path} /etc/nginx/sites-available/cherry-ai.me")
        print("  sudo ln -s /etc/nginx/sites-available/cherry-ai.me /etc/nginx/sites-enabled/")
        print("  sudo nginx -t && sudo systemctl reload nginx")
        
        return True
    
    def setup_ssl(self):
        """Setup SSL certificate with Let's Encrypt"""
        self.print_header("Setting up SSL Certificate")
        
        print("To setup SSL certificate, run:")
        print(f"  sudo certbot --nginx -d {self.domain} -d www.{self.domain}")
        print("\nMake sure:")
        print("  1. Domain is pointing to this server")
        print("  2. Ports 80 and 443 are open")
        print("  3. Nginx is running")
        
        return True
    
    def print_summary(self):
        """Print deployment summary"""
        self.print_header("Deployment Summary")
        
        if not self.issues:
            print(f"{GREEN}✅ Cherry AI website is properly deployed!{RESET}")
            print(f"\nAccess your site at:")
            print(f"  🌐 https://{self.domain}")
            print(f"  👤 Login: scoobyjava / Huskers1983$")
            print(f"  📊 Admin: https://{self.domain}/admin")
            print(f"  📚 API Docs: https://{self.domain}/api/docs")
        else:
            print(f"{RED}❌ Issues found during deployment:{RESET}")
            for issue in self.issues:
                print(f"  • {issue}")
            
            print(f"\n{YELLOW}Recommended fixes:{RESET}")
            if any("Docker" in issue for issue in self.issues):
                print("  1. Start Docker services: docker-compose -f docker-compose.single-user.yml up -d")
            if any("Nginx" in issue for issue in self.issues):
                print("  2. Fix Nginx config: sudo nginx -t && sudo systemctl restart nginx")
            if any("SSL" in issue for issue in self.issues):
                print("  3. Setup SSL: sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me")
            if any("Backend" in issue for issue in self.issues):
                print("  4. Check API logs: docker logs orchestra-main_api_1")
    
    def run(self):
        """Run complete deployment process"""
        print(f"{BOLD}{BLUE}Cherry AI Website Deployment & Verification{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print(f"\n{RED}Missing prerequisites! Please install required tools.{RESET}")
            return
        
        # Check Docker services
        if not self.check_docker_services():
            print(f"\n{YELLOW}Docker services not running. Starting them...{RESET}")
            # TODO: Replace with asyncio.sleep() for async code
            self.deploy_services()
            time.sleep(10)
            self.check_docker_services()
        
        # Check API health
        self.check_api_health()
        
        # Check Nginx
        if not self.check_nginx_config():
            self.create_nginx_config()
        
        # Check SSL
        self.check_ssl_certificate()
        
        # Check website accessibility
        self.check_website_accessibility()
        
        # Print summary
        self.print_summary()

def main():
    """Main function"""
    deployer = CherryAIDeployment()
    deployer.run()

if __name__ == "__main__":
    main()