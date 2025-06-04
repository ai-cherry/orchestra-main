#!/usr/bin/env python3
"""
Comprehensive Production Infrastructure Analysis for cherry-ai.me
Analyzes current deployment to create migration strategy
"""

import os
import sys
import json
import subprocess
import socket
import ssl
import requests
from datetime import datetime
from pathlib import Path
import dns.resolver
import whois
from urllib.parse import urlparse

class ProductionInfrastructureAnalyzer:
    def __init__(self):
        self.domain = "cherry-ai.me"
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "dns": {},
            "hosting": {},
            "ssl": {},
            "server": {},
            "deployment": {},
            "cdn": {},
            "dependencies": {},
            "risks": [],
            "migration_plan": []
        }
        
    def analyze_dns(self):
        """Analyze DNS configuration"""
        print("🌐 Analyzing DNS Configuration...")
        
        try:
            # Get DNS records
            resolver = dns.resolver.Resolver()
            
            # A records
            try:
                a_records = resolver.resolve(self.domain, 'A')
                self.analysis_results["dns"]["a_records"] = [str(r) for r in a_records]
                print(f"  A Records: {', '.join(self.analysis_results['dns']['a_records'])}")
            except:
                self.analysis_results["dns"]["a_records"] = []
                
            # CNAME records
            try:
                cname_records = resolver.resolve(self.domain, 'CNAME')
                self.analysis_results["dns"]["cname_records"] = [str(r) for r in cname_records]
            except:
                self.analysis_results["dns"]["cname_records"] = []
                
            # MX records
            try:
                mx_records = resolver.resolve(self.domain, 'MX')
                self.analysis_results["dns"]["mx_records"] = [f"{r.preference} {r.exchange}" for r in mx_records]
            except:
                self.analysis_results["dns"]["mx_records"] = []
                
            # NS records
            try:
                ns_records = resolver.resolve(self.domain, 'NS')
                self.analysis_results["dns"]["nameservers"] = [str(r) for r in ns_records]
                print(f"  Nameservers: {', '.join(self.analysis_results['dns']['nameservers'])}")
            except:
                self.analysis_results["dns"]["nameservers"] = []
                
            # TXT records (for verification, SPF, etc)
            try:
                txt_records = resolver.resolve(self.domain, 'TXT')
                self.analysis_results["dns"]["txt_records"] = [str(r) for r in txt_records]
            except:
                self.analysis_results["dns"]["txt_records"] = []
                
            # WHOIS information
            try:
                domain_info = whois.whois(self.domain)
                self.analysis_results["dns"]["registrar"] = domain_info.registrar
                self.analysis_results["dns"]["creation_date"] = str(domain_info.creation_date)
                self.analysis_results["dns"]["expiration_date"] = str(domain_info.expiration_date)
            except:
                pass
                
        except Exception as e:
            self.analysis_results["risks"].append(f"DNS analysis error: {str(e)}")
            
    def analyze_ssl(self):
        """Analyze SSL certificate"""
        print("\n🔒 Analyzing SSL Certificate...")
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    self.analysis_results["ssl"]["issuer"] = dict(x[0] for x in cert['issuer'])
                    self.analysis_results["ssl"]["subject"] = dict(x[0] for x in cert['subject'])
                    self.analysis_results["ssl"]["version"] = cert['version']
                    self.analysis_results["ssl"]["serial_number"] = cert['serialNumber']
                    self.analysis_results["ssl"]["not_before"] = cert['notBefore']
                    self.analysis_results["ssl"]["not_after"] = cert['notAfter']
                    self.analysis_results["ssl"]["san"] = cert.get('subjectAltName', [])
                    
                    print(f"  Issuer: {self.analysis_results['ssl']['issuer'].get('organizationName', 'Unknown')}")
                    print(f"  Valid Until: {self.analysis_results['ssl']['not_after']}")
                    
        except Exception as e:
            self.analysis_results["risks"].append(f"SSL analysis error: {str(e)}")
            
    def analyze_server(self):
        """Analyze server configuration"""
        print("\n🖥️  Analyzing Server Configuration...")
        
        try:
            response = requests.get(f"https://{self.domain}", timeout=10)
            headers = response.headers
            
            # Server information
            self.analysis_results["server"]["software"] = headers.get('Server', 'Unknown')
            self.analysis_results["server"]["powered_by"] = headers.get('X-Powered-By', 'Unknown')
            
            # Security headers
            security_headers = {
                "strict_transport_security": headers.get('Strict-Transport-Security'),
                "x_frame_options": headers.get('X-Frame-Options'),
                "x_content_type_options": headers.get('X-Content-Type-Options'),
                "x_xss_protection": headers.get('X-XSS-Protection'),
                "content_security_policy": headers.get('Content-Security-Policy'),
                "referrer_policy": headers.get('Referrer-Policy')
            }
            self.analysis_results["server"]["security_headers"] = security_headers
            
            # Cache headers
            cache_headers = {
                "cache_control": headers.get('Cache-Control'),
                "etag": headers.get('ETag'),
                "last_modified": headers.get('Last-Modified'),
                "expires": headers.get('Expires')
            }
            self.analysis_results["server"]["cache_headers"] = cache_headers
            
            # CDN detection
            cdn_headers = {
                "cf_ray": headers.get('CF-RAY'),  # Cloudflare
                "x_amz_cf_id": headers.get('X-Amz-Cf-Id'),  # CloudFront
                "x_served_by": headers.get('X-Served-By'),  # Fastly
                "x_cache": headers.get('X-Cache')
            }
            self.analysis_results["cdn"]["headers"] = cdn_headers
            
            # Detect CDN provider
            if headers.get('CF-RAY'):
                self.analysis_results["cdn"]["provider"] = "Cloudflare"
            elif headers.get('X-Amz-Cf-Id'):
                self.analysis_results["cdn"]["provider"] = "AWS CloudFront"
            elif headers.get('X-Served-By'):
                self.analysis_results["cdn"]["provider"] = "Fastly"
            else:
                self.analysis_results["cdn"]["provider"] = "None detected"
                
            print(f"  Server: {self.analysis_results['server']['software']}")
            print(f"  CDN: {self.analysis_results['cdn']['provider']}")
            
            # Check response time
            response_time = response.elapsed.total_seconds()
            self.analysis_results["server"]["response_time"] = response_time
            print(f"  Response Time: {response_time:.2f}s")
            
        except Exception as e:
            self.analysis_results["risks"].append(f"Server analysis error: {str(e)}")
            
    def analyze_deployment(self):
        """Analyze deployment configuration"""
        print("\n🚀 Analyzing Deployment Configuration...")
        
        # Check for common deployment files
        deployment_endpoints = [
            "/.git/config",
            "/.env",
            "/package.json",
            "/composer.json",
            "/requirements.txt",
            "/Dockerfile",
            "/docker-compose.yml",
            "/.gitlab-ci.yml",
            "/.github/workflows",
            "/robots.txt",
            "/sitemap.xml",
            "/humans.txt"
        ]
        
        for endpoint in deployment_endpoints:
            try:
                response = requests.get(f"https://{self.domain}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.analysis_results["deployment"][endpoint] = "Exposed"
                    self.analysis_results["risks"].append(f"Exposed file: {endpoint}")
                elif response.status_code == 403:
                    self.analysis_results["deployment"][endpoint] = "Protected"
                else:
                    self.analysis_results["deployment"][endpoint] = "Not found"
            except:
                pass
                
        # Check for API endpoints
        api_endpoints = [
            "/api",
            "/api/v1",
            "/api/health",
            "/api/status",
            "/graphql",
            "/admin",
            "/wp-admin",
            "/.well-known"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"https://{self.domain}{endpoint}", timeout=5)
                if response.status_code < 400:
                    self.analysis_results["deployment"][f"api_{endpoint}"] = response.status_code
                    print(f"  Found endpoint: {endpoint} ({response.status_code})")
            except:
                pass
                
    def analyze_current_build(self):
        """Analyze current build artifacts"""
        print("\n📦 Analyzing Current Build...")
        
        try:
            # Get main page
            response = requests.get(f"https://{self.domain}", timeout=10)
            content = response.text
            
            # Extract JavaScript files
            import re
            js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', content)
            self.analysis_results["deployment"]["js_files"] = js_files
            
            # Extract CSS files
            css_files = re.findall(r'href=["\']([^"\']+\.css)["\']', content)
            self.analysis_results["deployment"]["css_files"] = css_files
            
            # Check for build identifiers
            if "index-" in content:
                build_hash = re.search(r'index-(\d+)', content)
                if build_hash:
                    self.analysis_results["deployment"]["build_timestamp"] = build_hash.group(1)
                    print(f"  Current Build: {build_hash.group(1)}")
                    
            # Check for framework indicators
            frameworks = {
                "React": ["_app", "react", "__NEXT_DATA__"],
                "Vue": ["vue", "v-", "@click"],
                "Angular": ["ng-", "angular"],
                "Vite": ["vite", "@vitejs"]
            }
            
            detected_frameworks = []
            for framework, indicators in frameworks.items():
                if any(indicator in content for indicator in indicators):
                    detected_frameworks.append(framework)
                    
            self.analysis_results["deployment"]["frameworks"] = detected_frameworks
            print(f"  Detected Frameworks: {', '.join(detected_frameworks)}")
            
        except Exception as e:
            self.analysis_results["risks"].append(f"Build analysis error: {str(e)}")
            
    def create_migration_plan(self):
        """Create detailed migration plan"""
        print("\n📋 Creating Migration Plan...")
        
        # Pre-migration checklist
        pre_migration = [
            {
                "step": 1,
                "action": "Backup Current Production",
                "commands": [
                    "# Create full backup of current deployment",
                    "ssh root@cherry-ai.me 'tar -czf /backup/cherry-ai-$(date +%Y%m%d-%H%M%S).tar.gz /var/www/cherry_ai-admin'",
                    "# Backup Nginx configuration",
                    "ssh root@cherry-ai.me 'cp -r /etc/nginx /backup/nginx-$(date +%Y%m%d-%H%M%S)'",
                    "# Export database if exists",
                    "ssh root@cherry-ai.me 'pg_dump cherry_ai > /backup/cherry_ai-$(date +%Y%m%d-%H%M%S).sql'"
                ],
                "verification": "Verify backup files exist and are complete"
            },
            {
                "step": 2,
                "action": "Setup Staging Environment",
                "commands": [
                    "# Create staging subdomain",
                    "# Point staging.cherry-ai.me to same server",
                    "# Deploy new build to staging first"
                ],
                "verification": "Test complete functionality on staging"
            },
            {
                "step": 3,
                "action": "Update DNS TTL",
                "commands": [
                    "# Reduce TTL to 300 seconds 24 hours before migration",
                    "# This allows faster DNS propagation during cutover"
                ],
                "verification": "Verify TTL change has propagated"
            }
        ]
        
        # Migration steps
        migration_steps = [
            {
                "step": 4,
                "action": "Deploy New Build",
                "commands": [
                    "# SSH to production server",
                    "ssh root@cherry-ai.me",
                    "",
                    "# Stop any running services",
                    "systemctl stop cherry_ai-api || true",
                    "",
                    "# Backup current deployment",
                    "mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin.old",
                    "",
                    "# Deploy new build",
                    "mkdir -p /var/www/cherry_ai-admin",
                    "cd /root/cherry_ai-main/admin-ui",
                    "npm run build",
                    "cp -r dist/* /var/www/cherry_ai-admin/",
                    "",
                    "# Update permissions",
                    "chown -R www-data:www-data /var/www/cherry_ai-admin",
                    "chmod -R 755 /var/www/cherry_ai-admin"
                ],
                "verification": "Check file deployment with ls -la /var/www/cherry_ai-admin"
            },
            {
                "step": 5,
                "action": "Update Nginx Configuration",
                "commands": [
                    "# Update Nginx to prevent caching issues",
                    "cat > /etc/nginx/sites-available/cherry_ai-admin << 'EOF'",
                    "server {",
                    "    listen 443 ssl http2;",
                    "    server_name cherry-ai.me;",
                    "    ",
                    "    root /var/www/cherry_ai-admin;",
                    "    index index.html;",
                    "    ",
                    "    # Prevent caching of HTML",
                    "    location / {",
                    "        try_files $uri $uri/ /index.html;",
                    "        add_header Cache-Control 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0';",
                    "        expires off;",
                    "        etag off;",
                    "    }",
                    "    ",
                    "    # Cache static assets",
                    "    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {",
                    "        expires 1y;",
                    "        add_header Cache-Control 'public, immutable';",
                    "    }",
                    "}",
                    "EOF",
                    "",
                    "# Test and reload Nginx",
                    "nginx -t && systemctl reload nginx"
                ],
                "verification": "Test with curl -I https://cherry-ai.me"
            },
            {
                "step": 6,
                "action": "Clear CDN Cache",
                "commands": [
                    "# If using Cloudflare",
                    "# Go to Cloudflare dashboard > Caching > Purge Everything",
                    "",
                    "# If using CloudFront",
                    "aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths '/*'",
                    "",
                    "# Force cache clear headers",
                    "curl -X PURGE https://cherry-ai.me/"
                ],
                "verification": "Check new build loads in incognito browser"
            }
        ]
        
        # Post-migration validation
        post_migration = [
            {
                "step": 7,
                "action": "Validate Deployment",
                "checks": [
                    "✓ Homepage loads correctly",
                    "✓ All assets load (no 404s)",
                    "✓ SSL certificate is valid",
                    "✓ Login functionality works",
                    "✓ API endpoints respond",
                    "✓ No console errors",
                    "✓ Performance metrics acceptable"
                ],
                "commands": [
                    "# Test homepage",
                    "curl -I https://cherry-ai.me",
                    "",
                    "# Test API",
                    "curl https://cherry-ai.me/api/health",
                    "",
                    "# Check for errors",
                    "tail -f /var/log/nginx/error.log"
                ]
            },
            {
                "step": 8,
                "action": "Monitor and Rollback Plan",
                "monitoring": [
                    "Watch error logs for 30 minutes",
                    "Monitor server resources",
                    "Check user reports"
                ],
                "rollback": [
                    "# If issues arise, rollback immediately:",
                    "mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin.failed",
                    "mv /var/www/cherry_ai-admin.old /var/www/cherry_ai-admin",
                    "systemctl reload nginx",
                    "# Clear CDN cache again"
                ]
            }
        ]
        
        self.analysis_results["migration_plan"] = {
            "pre_migration": pre_migration,
            "migration_steps": migration_steps,
            "post_migration": post_migration,
            "estimated_downtime": "0-5 minutes",
            "rollback_time": "< 1 minute"
        }
        
    def identify_risks(self):
        """Identify migration risks"""
        print("\n⚠️  Identifying Risks...")
        
        risks = [
            {
                "risk": "Cache Persistence",
                "impact": "Users may see old version",
                "mitigation": "Implement cache-busting with timestamps, clear CDN cache"
            },
            {
                "risk": "DNS Propagation",
                "impact": "Some users may hit old server",
                "mitigation": "Reduce TTL 24 hours before, use same server if possible"
            },
            {
                "risk": "SSL Certificate",
                "impact": "Security warnings",
                "mitigation": "Ensure certificate covers all domains, test before cutover"
            },
            {
                "risk": "Database Connections",
                "impact": "API failures",
                "mitigation": "Test all database connections, ensure connection strings updated"
            },
            {
                "risk": "Third-party Dependencies",
                "impact": "Feature breakage",
                "mitigation": "Inventory all external services, update API keys/webhooks"
            },
            {
                "risk": "SEO Impact",
                "impact": "Search ranking loss",
                "mitigation": "Maintain URL structure, implement 301 redirects, update sitemap"
            }
        ]
        
        self.analysis_results["risks"].extend([r["risk"] for r in risks])
        self.analysis_results["risk_mitigation"] = risks
        
    def generate_report(self):
        """Generate comprehensive analysis report"""
        
        # Run all analyses
        self.analyze_dns()
        self.analyze_ssl()
        self.analyze_server()
        self.analyze_deployment()
        self.analyze_current_build()
        self.identify_risks()
        self.create_migration_plan()
        
        # Save report
        report_file = f"production_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
            
        print(f"\n📊 Analysis complete! Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("INFRASTRUCTURE SUMMARY")
        print("=" * 50)
        print(f"Domain: {self.domain}")
        print(f"IP: {', '.join(self.analysis_results['dns'].get('a_records', ['Unknown']))}")
        print(f"Server: {self.analysis_results['server'].get('software', 'Unknown')}")
        print(f"CDN: {self.analysis_results['cdn'].get('provider', 'None')}")
        print(f"SSL Issuer: {self.analysis_results['ssl'].get('issuer', {}).get('organizationName', 'Unknown')}")
        print(f"\nRisks Identified: {len(self.analysis_results['risks'])}")
        print(f"Migration Steps: {len(self.analysis_results['migration_plan']['migration_steps'])}")
        print(f"Estimated Downtime: {self.analysis_results['migration_plan']['estimated_downtime']}")
        
        return self.analysis_results

def main():
    # Install required packages
    subprocess.run(["pip", "install", "-q", "dnspython", "python-whois"], capture_output=True)
    
    analyzer = ProductionInfrastructureAnalyzer()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
