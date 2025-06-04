#!/usr/bin/env python3
"""
Analyze cherry-ai.me deployment and create migration strategy
"""

import os
import json
import socket
import ssl
import subprocess
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

class CherryDeploymentAnalyzer:
    def __init__(self):
        self.domain = "cherry-ai.me"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "current_state": {},
            "migration_plan": {},
            "risks": [],
            "recommendations": []
        }
        
    def analyze_current_deployment(self):
        """Analyze current deployment state"""
        print("🔍 Analyzing current cherry-ai.me deployment...")
        
        # Check DNS resolution
        try:
            ip = socket.gethostbyname(self.domain)
            self.results["current_state"]["ip_address"] = ip
            print(f"  ✅ Domain resolves to: {ip}")
        except Exception as e:
            self.results["risks"].append(f"DNS resolution failed: {str(e)}")
            
        # Check HTTPS connectivity
        try:
            req = Request(f"https://{self.domain}", headers={'User-Agent': 'Mozilla/5.0'})
            response = urlopen(req, timeout=10)
            self.results["current_state"]["status_code"] = response.getcode()
            self.results["current_state"]["server"] = response.headers.get('Server', 'Unknown')
            
            # Read content to check build version
            content = response.read().decode('utf-8')
            
            # Check for build timestamp
            if 'index-' in content:
                import re
                match = re.search(r'index-(\d+)', content)
                if match:
                    self.results["current_state"]["build_timestamp"] = match.group(1)
                    print(f"  ✅ Current build: {match.group(1)}")
                    
            # Check title
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                self.results["current_state"]["title"] = title_match.group(1)
                print(f"  ✅ Page title: {title_match.group(1)}")
                
            # Check for cache headers
            cache_control = response.headers.get('Cache-Control', 'Not set')
            self.results["current_state"]["cache_control"] = cache_control
            print(f"  📋 Cache-Control: {cache_control}")
            
        except Exception as e:
            self.results["risks"].append(f"HTTPS check failed: {str(e)}")
            
        # Check SSL certificate
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    self.results["current_state"]["ssl_issuer"] = dict(x[0] for x in cert['issuer']).get('organizationName', 'Unknown')
                    self.results["current_state"]["ssl_expires"] = cert['notAfter']
                    print(f"  ✅ SSL: {self.results['current_state']['ssl_issuer']}")
        except Exception as e:
            self.results["risks"].append(f"SSL check failed: {str(e)}")
            
    def check_local_build(self):
        """Check local build readiness"""
        print("\n📦 Checking local build readiness...")
        
        admin_ui_path = "/root/cherry_ai-main/admin-ui"
        if os.path.exists(admin_ui_path):
            # Check if build exists
            dist_path = os.path.join(admin_ui_path, "dist")
            if os.path.exists(dist_path):
                files = os.listdir(dist_path)
                self.results["current_state"]["local_build_ready"] = True
                self.results["current_state"]["local_build_files"] = len(files)
                print(f"  ✅ Local build ready: {len(files)} files")
            else:
                self.results["current_state"]["local_build_ready"] = False
                self.results["recommendations"].append("Run 'npm run build' in admin-ui directory")
                print("  ❌ No build found in admin-ui/dist")
        else:
            self.results["risks"].append("admin-ui directory not found")
            
    def create_migration_plan(self):
        """Create detailed migration plan"""
        print("\n📋 Creating migration plan...")
        
        self.results["migration_plan"] = {
            "pre_deployment": [
                {
                    "step": 1,
                    "action": "Backup current production",
                    "commands": [
                        "# SSH to production server",
                        "ssh root@cherry-ai.me",
                        "",
                        "# Create backup directory",
                        "mkdir -p /backup/$(date +%Y%m%d)",
                        "",
                        "# Backup current deployment",
                        "tar -czf /backup/$(date +%Y%m%d)/cherry_ai-admin-backup.tar.gz /var/www/cherry_ai-admin",
                        "",
                        "# Backup Nginx config",
                        "cp -r /etc/nginx /backup/$(date +%Y%m%d)/nginx-backup"
                    ]
                },
                {
                    "step": 2,
                    "action": "Build latest version locally",
                    "commands": [
                        "cd /root/cherry_ai-main/admin-ui",
                        "npm install",
                        "npm run build",
                        "# Verify build output",
                        "ls -la dist/"
                    ]
                }
            ],
            "deployment": [
                {
                    "step": 3,
                    "action": "Deploy new build",
                    "commands": [
                        "# Copy build to server",
                        "rsync -avz --delete /root/cherry_ai-main/admin-ui/dist/ root@cherry-ai.me:/var/www/cherry_ai-admin-new/",
                        "",
                        "# SSH to server",
                        "ssh root@cherry-ai.me",
                        "",
                        "# Swap deployments",
                        "mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-old",
                        "mv /var/www/cherry_ai-admin-new /var/www/cherry_ai-admin",
                        "",
                        "# Set permissions",
                        "chown -R www-data:www-data /var/www/cherry_ai-admin",
                        "chmod -R 755 /var/www/cherry_ai-admin"
                    ]
                },
                {
                    "step": 4,
                    "action": "Update Nginx configuration",
                    "commands": [
                        "# Edit Nginx config to prevent caching",
                        "cat > /etc/nginx/sites-available/cherry_ai-admin << 'EOF'",
                        "server {",
                        "    listen 443 ssl http2;",
                        "    server_name cherry-ai.me;",
                        "    ",
                        "    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;",
                        "    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;",
                        "    ",
                        "    root /var/www/cherry_ai-admin;",
                        "    index index.html;",
                        "    ",
                        "    # Security headers",
                        "    add_header X-Frame-Options \"SAMEORIGIN\" always;",
                        "    add_header X-Content-Type-Options \"nosniff\" always;",
                        "    add_header X-XSS-Protection \"1; mode=block\" always;",
                        "    ",
                        "    # Prevent HTML caching",
                        "    location / {",
                        "        try_files $uri $uri/ /index.html;",
                        "        add_header Cache-Control \"no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0\";",
                        "        expires off;",
                        "        etag off;",
                        "    }",
                        "    ",
                        "    # Cache static assets",
                        "    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {",
                        "        expires 1y;",
                        "        add_header Cache-Control \"public, immutable\";",
                        "    }",
                        "    ",
                        "    # API proxy",
                        "    location /api {",
                        "        proxy_pass http://localhost:8001;",
                        "        proxy_http_version 1.1;",
                        "        proxy_set_header Upgrade $http_upgrade;",
                        "        proxy_set_header Connection 'upgrade';",
                        "        proxy_set_header Host $host;",
                        "        proxy_cache_bypass $http_upgrade;",
                        "    }",
                        "}",
                        "EOF",
                        "",
                        "# Test and reload",
                        "nginx -t && systemctl reload nginx"
                    ]
                }
            ],
            "post_deployment": [
                {
                    "step": 5,
                    "action": "Clear caches",
                    "commands": [
                        "# Clear any CDN cache if applicable",
                        "# For Cloudflare: Use dashboard or API",
                        "",
                        "# Force browser cache clear",
                        "curl -I https://cherry-ai.me",
                        "",
                        "# Test in incognito mode"
                    ]
                },
                {
                    "step": 6,
                    "action": "Verify deployment",
                    "checks": [
                        "✓ Homepage loads without errors",
                        "✓ Console shows no 404s",
                        "✓ Login functionality works",
                        "✓ API endpoints respond",
                        "✓ New build timestamp visible"
                    ]
                },
                {
                    "step": 7,
                    "action": "Monitor and rollback if needed",
                    "commands": [
                        "# Monitor logs",
                        "tail -f /var/log/nginx/error.log",
                        "",
                        "# If rollback needed:",
                        "mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-failed",
                        "mv /var/www/cherry_ai-admin-old /var/www/cherry_ai-admin",
                        "systemctl reload nginx"
                    ]
                }
            ]
        }
        
    def identify_risks(self):
        """Identify deployment risks"""
        print("\n⚠️  Identifying risks...")
        
        risks = [
            {
                "risk": "Browser Cache Persistence",
                "impact": "Users see old version",
                "mitigation": "Implement aggressive cache busting, clear CDN"
            },
            {
                "risk": "API Connection Issues",
                "impact": "Login/functionality broken",
                "mitigation": "Ensure API is running on port 8001, test endpoints"
            },
            {
                "risk": "SSL Certificate",
                "impact": "Security warnings",
                "mitigation": "Verify cert is valid and covers domain"
            },
            {
                "risk": "File Permissions",
                "impact": "403 errors",
                "mitigation": "Set correct ownership (www-data) and permissions (755)"
            },
            {
                "risk": "Build Version Mismatch",
                "impact": "Wrong version deployed",
                "mitigation": "Verify build timestamp before deployment"
            }
        ]
        
        for risk in risks:
            self.results["risks"].append(risk["risk"])
            
        self.results["risk_mitigation"] = risks
        
    def generate_deployment_script(self):
        """Generate automated deployment script"""
        print("\n🚀 Generating deployment script...")
        
        script_content = '''#!/bin/bash
# Cherry AI Deployment Script
# Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

set -e

echo "🚀 Cherry AI Deployment"
echo "========================="

# Configuration
DOMAIN="cherry-ai.me"
LOCAL_BUILD="/root/cherry_ai-main/admin-ui/dist"
REMOTE_USER="root"
REMOTE_HOST="$DOMAIN"
REMOTE_PATH="/var/www/cherry_ai-admin"

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

# Function to print colored output
print_status() {
    case $1 in
        "error") echo -e "${RED}❌ $2${NC}" ;;
        "success") echo -e "${GREEN}✅ $2${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $2${NC}" ;;
        *) echo "$2" ;;
    esac
}

# Step 1: Build check
print_status "info" "Checking local build..."
if [ ! -d "$LOCAL_BUILD" ]; then
    print_status "error" "Build directory not found!"
    print_status "info" "Running build..."
    cd /root/cherry_ai-main/admin-ui
    npm run build
fi

# Step 2: Create backup
print_status "info" "Creating backup on remote server..."
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p /backup/$(date +%Y%m%d) && tar -czf /backup/$(date +%Y%m%d)/cherry_ai-backup-$(date +%H%M%S).tar.gz $REMOTE_PATH"

# Step 3: Deploy new build
print_status "info" "Deploying new build..."
rsync -avz --delete $LOCAL_BUILD/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH-new/

# Step 4: Swap deployments
print_status "info" "Swapping deployments..."
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
    mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-old
    mv /var/www/cherry_ai-admin-new /var/www/cherry_ai-admin
    chown -R www-data:www-data /var/www/cherry_ai-admin
    chmod -R 755 /var/www/cherry_ai-admin
    systemctl reload nginx
EOF

# Step 5: Verify deployment
print_status "info" "Verifying deployment..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "success" "Deployment successful! Site is accessible."
    
    # Check for new build
    BUILD_CHECK=$(curl -s https://$DOMAIN | grep -o 'index-[0-9]*' | head -1)
    print_status "success" "Current build: $BUILD_CHECK"
else
    print_status "error" "Site returned HTTP $HTTP_STATUS"
    print_status "warning" "Rolling back..."
    
    ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
        mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-failed
        mv /var/www/cherry_ai-admin-old /var/www/cherry_ai-admin
        systemctl reload nginx
EOF
    
    print_status "error" "Deployment failed and rolled back!"
    exit 1
fi

print_status "success" "Deployment complete!"
print_status "info" "Next steps:"
echo "  1. Test in incognito browser"
echo "  2. Clear CDN cache if applicable"
echo "  3. Monitor error logs: ssh $REMOTE_USER@$REMOTE_HOST 'tail -f /var/log/nginx/error.log'"
'''
        
        with open('scripts/deploy_to_cherry.sh', 'w') as f:
            f.write(script_content)
        os.chmod('scripts/deploy_to_cherry.sh', 0o755)
        
        self.results["deployment_script"] = "scripts/deploy_to_cherry.sh"
        print("  ✅ Created: scripts/deploy_to_cherry.sh")
        
    def generate_report(self):
        """Generate analysis report"""
        self.analyze_current_deployment()
        self.check_local_build()
        self.create_migration_plan()
        self.identify_risks()
        self.generate_deployment_script()
        
        # Save report
        report_file = f"cherry_deployment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n📊 Analysis complete! Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("DEPLOYMENT SUMMARY")
        print("=" * 50)
        print(f"Domain: {self.domain}")
        print(f"Current Build: {self.results['current_state'].get('build_timestamp', 'Unknown')}")
        print(f"Page Title: {self.results['current_state'].get('title', 'Unknown')}")
        print(f"SSL Issuer: {self.results['current_state'].get('ssl_issuer', 'Unknown')}")
        print(f"Local Build Ready: {self.results['current_state'].get('local_build_ready', False)}")
        print(f"\nRisks Identified: {len(self.results['risks'])}")
        print(f"Deployment Steps: {len(self.results['migration_plan']['deployment'])}")
        
        print("\n🚀 Quick Deploy Command:")
        print("  bash scripts/deploy_to_cherry.sh")
        
        return self.results

def main():
    analyzer = CherryDeploymentAnalyzer()
    analyzer.generate_report()

if __name__ == "__main__":
    main()