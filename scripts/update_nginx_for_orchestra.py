#!/usr/bin/env python3
"""Update Nginx configuration to serve the new Cherry AI application."""

import subprocess
import sys
import time

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    print("=== Updating Nginx Configuration for Cherry AI ===")
    
    # Create new Nginx configuration
    nginx_config = """server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Main application - proxy to Docker container
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8001/health;
        access_log off;
    }
}"""
    
    # Write new configuration
    print("\n1. Writing new Nginx configuration...")
    with open('/tmp/cherry_ai-ai.conf', 'w') as f:
        f.write(nginx_config)
    
    # Copy to Nginx sites-available
    run_command("sudo cp /tmp/cherry_ai-ai.conf /etc/nginx/sites-available/cherry_ai-ai")
    
    # Remove old symlinks
    print("\n2. Removing old Nginx configurations...")
    run_command("sudo rm -f /etc/nginx/sites-enabled/cherry_ai", check=False)
    run_command("sudo rm -f /etc/nginx/sites-enabled/cherry-ai", check=False)
    run_command("sudo rm -f /etc/nginx/sites-enabled/cherry-ai.me", check=False)
    
    # Create new symlink
    print("\n3. Enabling new configuration...")
    run_command("sudo ln -sf /etc/nginx/sites-available/cherry_ai-ai /etc/nginx/sites-enabled/cherry_ai-ai")
    
    # Test Nginx configuration
    print("\n4. Testing Nginx configuration...")
    result = run_command("sudo nginx -t", check=False)
    if result.returncode != 0:
        print("Nginx configuration test failed!")
        sys.exit(1)
    
    # Reload Nginx
    print("\n5. Reloading Nginx...")
    run_command("sudo systemctl reload nginx")
    
    # Check if Docker containers are running
    print("\n6. Checking Docker containers...")
    result = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(result.stdout)
    
    # Ensure API container is running on port 8001
    print("\n7. Verifying API is accessible...")
    # TODO: Replace with asyncio.sleep() for async code
    time.sleep(2)
    result = run_command("curl -s http://localhost:8001/health", check=False)
    if result.returncode == 0:
        print("✓ API is responding on port 8001")
        print(f"Response: {result.stdout}")
    else:
        print("✗ API is not responding on port 8001")
        print("Checking Docker logs...")
        run_command("docker logs cherry_ai_api --tail 20", check=False)
    
    print("\n=== Nginx Update Complete ===")
    print("The new Cherry AI application should now be accessible at https://cherry-ai.me")
    print("\nNext steps:")
    print("1. Visit https://cherry-ai.me to see the new application")
    print("2. Login with credentials: scoobyjava / Huskers1983$")
    print("3. If you see any issues, check:")
    print("   - Docker logs: docker logs cherry_ai_api")
    print("   - Nginx logs: sudo tail -f /var/log/nginx/error.log")

if __name__ == "__main__":
    main()