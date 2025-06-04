#!/usr/bin/env python3
"""Deploy the admin-ui to the web server."""

import subprocess
import sys
import os
import shutil

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    print("=== Deploying Admin UI to Web Server ===")
    
    # Check if admin-ui/dist exists
    if not os.path.exists("/root/cherry_ai-main/admin-ui/dist"):
        print("Error: admin-ui/dist not found. Building admin-ui...")
        
        # Install dependencies and build
        print("\n1. Installing dependencies...")
        run_command("cd /root/cherry_ai-main/admin-ui && npm install")
        
        print("\n2. Building admin-ui...")
        run_command("cd /root/cherry_ai-main/admin-ui && npm run build")
    
    # Backup old files
    print("\n3. Backing up old web files...")
    run_command("sudo mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin.old", check=False)
    
    # Create new directory
    print("\n4. Creating new web directory...")
    run_command("sudo mkdir -p /var/www/cherry_ai-admin")
    
    # Copy new files
    print("\n5. Copying admin-ui dist files...")
    run_command("sudo cp -r /root/cherry_ai-main/admin-ui/dist/* /var/www/cherry_ai-admin/")
    
    # Set permissions
    print("\n6. Setting permissions...")
    run_command("sudo chown -R www-data:www-data /var/www/cherry_ai-admin")
    run_command("sudo chmod -R 755 /var/www/cherry_ai-admin")
    
    # Update Nginx to serve both static files and proxy API
    print("\n7. Updating Nginx configuration...")
    nginx_config = """server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
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
    
    # Serve static files from admin-ui
    root /var/www/cherry_ai-admin;
    index index.html;
    
    # Main application
    location / {
        try_files $uri $uri/ /index.html;
        
        # Disable caching for HTML files
        location ~* \\.html$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
    
    # Cache static assets
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "$http_origin" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key" always;
        add_header Access-Control-Allow-Credentials "true" always;
        
        # Handle preflight
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "$http_origin";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-API-Key";
            add_header Access-Control-Allow-Credentials "true";
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
    
    # Health check
    location /health {
        proxy_pass http://localhost:8001/health;
        access_log off;
    }
}"""
    
    # Write new configuration
    with open('/tmp/cherry_ai-admin.conf', 'w') as f:
        f.write(nginx_config)
    
    # Copy to Nginx
    run_command("sudo cp /tmp/cherry_ai-admin.conf /etc/nginx/sites-available/cherry_ai-admin")
    
    # Remove old configs and enable new one
    print("\n8. Enabling new Nginx configuration...")
    run_command("sudo rm -f /etc/nginx/sites-enabled/*", check=False)
    run_command("sudo ln -sf /etc/nginx/sites-available/cherry_ai-admin /etc/nginx/sites-enabled/cherry_ai-admin")
    
    # Test and reload Nginx
    print("\n9. Testing Nginx configuration...")
    result = run_command("sudo nginx -t", check=False)
    if result.returncode != 0:
        print("Nginx configuration test failed!")
        sys.exit(1)
    
    print("\n10. Reloading Nginx...")
    run_command("sudo systemctl reload nginx")
    
    print("\n=== Admin UI Deployment Complete ===")
    print("The Cherry AI admin interface is now live at https://cherry-ai.me")
    print("\nFeatures available:")
    print("- Multi-persona support (Cherry, Sophia, Karen)")
    print("- Search modes (Normal, Creative, Deep, Super-Deep, Uncensored)")
    print("- MCP server integration (PostgreSQL, Weaviate, Airbyte)")
    print("- Real-time monitoring and analytics")
    print("\nLogin credentials: scoobyjava / Huskers1983$")

if __name__ == "__main__":
    main()
