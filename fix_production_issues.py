#!/usr/bin/env python3
"""
Comprehensive Production Fix Script
Resolves all remaining critical issues identified in the production review
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

class ProductionFixer:
    """Fixes all remaining production issues"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.issues_fixed = []
        self.issues_failed = []
    
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command, cwd=None, timeout=60):
        """Run shell command with error handling"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd or self.base_dir,
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_service_health(self, url, name):
        """Check if a service is healthy"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.log(f"✅ {name} is healthy")
                return True
            else:
                self.log(f"❌ {name} returned {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ {name} is not accessible: {str(e)[:50]}")
            return False
    
    def fix_openrouter_api(self):
        """Start the OpenRouter API service"""
        self.log("🔧 Fixing OpenRouter API...")
        
        # Check if already running
        if self.check_service_health("http://192.9.142.8:8020/health", "OpenRouter API"):
            self.issues_fixed.append("OpenRouter API already running")
            return True
        
        # Try to start the service
        openrouter_script = self.base_dir / "src" / "api" / "ai_router_api.py"
        if openrouter_script.exists():
            self.log("Starting OpenRouter API...")
            success, stdout, stderr = self.run_command(
                f"cd src/api && python3 ai_router_api.py &",
                timeout=10
            )
            
            if success:
                time.sleep(3)  # Wait for startup
                if self.check_service_health("http://192.9.142.8:8020/health", "OpenRouter API"):
                    self.issues_fixed.append("OpenRouter API started successfully")
                    return True
        
        # Alternative: Start from main directory
        self.log("Trying alternative OpenRouter startup...")
        success, stdout, stderr = self.run_command(
            "python3 -m src.api.ai_router_api &",
            timeout=10
        )
        
        if success:
            time.sleep(3)
            if self.check_service_health("http://192.9.142.8:8020/health", "OpenRouter API"):
                self.issues_fixed.append("OpenRouter API started (alternative method)")
                return True
        
        self.issues_failed.append("OpenRouter API could not be started")
        return False
    
    def fix_vercel_deployment(self):
        """Fix Vercel deployment issues"""
        self.log("🔧 Fixing Vercel deployment...")
        
        admin_dir = self.base_dir / "admin-interface"
        if not admin_dir.exists():
            self.issues_failed.append("Admin interface directory not found")
            return False
        
        # Clean build artifacts
        self.log("Cleaning build artifacts...")
        success, stdout, stderr = self.run_command(
            "rm -rf .vercel .next dist node_modules/.cache",
            cwd=admin_dir
        )
        
        # Rebuild
        self.log("Rebuilding application...")
        success, stdout, stderr = self.run_command(
            "npm run build",
            cwd=admin_dir,
            timeout=120
        )
        
        if not success:
            self.log(f"Build failed: {stderr}")
            self.issues_failed.append("Build failed")
            return False
        
        self.log("Build completed successfully")
        self.issues_fixed.append("Application rebuilt successfully")
        return True
    
    def deploy_to_github_pages(self):
        """Deploy to GitHub Pages as backup"""
        self.log("🔧 Setting up GitHub Pages deployment...")
        
        admin_dir = self.base_dir / "admin-interface"
        dist_dir = admin_dir / "dist"
        
        if not dist_dir.exists():
            self.log("No dist directory found, building first...")
            if not self.fix_vercel_deployment():
                return False
        
        # Create gh-pages deployment script
        deploy_script = """#!/bin/bash
set -e

echo "🚀 Deploying to GitHub Pages..."

# Build the application
npm run build

# Create temporary directory for gh-pages
rm -rf /tmp/gh-pages-deploy
mkdir -p /tmp/gh-pages-deploy
cp -r dist/* /tmp/gh-pages-deploy/

# Switch to gh-pages branch
git checkout -B gh-pages
git rm -rf . || true
cp -r /tmp/gh-pages-deploy/* .
echo "orchestra-admin.github.io" > CNAME

# Commit and push
git add .
git commit -m "Deploy to GitHub Pages: $(date)"
git push origin gh-pages --force

# Switch back to main
git checkout main

echo "✅ Deployed to GitHub Pages"
echo "URL: https://ai-cherry.github.io/orchestra-main/"
"""
        
        script_path = admin_dir / "deploy-gh-pages.sh"
        with open(script_path, 'w') as f:
            f.write(deploy_script)
        
        os.chmod(script_path, 0o755)
        
        self.log("GitHub Pages deployment script created")
        self.issues_fixed.append("GitHub Pages deployment script ready")
        return True
    
    def create_monitoring_script(self):
        """Create monitoring script for services"""
        self.log("🔧 Creating monitoring script...")
        
        monitoring_script = """#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

def check_service(url, name):
    try:
        response = requests.get(url, timeout=5)
        status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{datetime.now().strftime('%H:%M:%S')} {name}: {status}")
        return response.status_code == 200
    except Exception as e:
        print(f"{datetime.now().strftime('%H:%M:%S')} {name}: ❌ {str(e)[:50]}")
        return False

def main():
    services = [
        ("http://192.9.142.8:8000/health", "Personas API"),
        ("http://192.9.142.8:8010/health", "Main API"),
        ("http://192.9.142.8:8020/health", "OpenRouter API"),
        ("https://orchestra-admin-interface.vercel.app", "Admin Interface"),
        ("https://orchestra-ai-frontend.vercel.app", "AI Frontend"),
    ]
    
    print("🔍 Orchestra AI Service Monitor")
    print("=" * 50)
    
    while True:
        all_healthy = True
        for url, name in services:
            healthy = check_service(url, name)
            if not healthy:
                all_healthy = False
        
        if all_healthy:
            print(f"{datetime.now().strftime('%H:%M:%S')} 🎉 All services healthy!")
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Some services have issues")
        
        print("-" * 30)
        time.sleep(30)

if __name__ == "__main__":
    main()
"""
        
        monitor_path = self.base_dir / "monitor_services.py"
        with open(monitor_path, 'w') as f:
            f.write(monitoring_script)
        
        os.chmod(monitor_path, 0o755)
        
        self.log("Service monitoring script created")
        self.issues_fixed.append("Service monitoring script ready")
        return True
    
    def verify_backend_services(self):
        """Verify all backend services are working"""
        self.log("🔍 Verifying backend services...")
        
        services = [
            ("http://192.9.142.8:8000/health", "Personas API"),
            ("http://192.9.142.8:8010/health", "Main API"),
        ]
        
        all_healthy = True
        for url, name in services:
            if self.check_service_health(url, name):
                self.issues_fixed.append(f"{name} verified healthy")
            else:
                self.issues_failed.append(f"{name} not accessible")
                all_healthy = False
        
        return all_healthy
    
    def create_status_report(self):
        """Create final status report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issues_fixed": self.issues_fixed,
            "issues_failed": self.issues_failed,
            "recommendations": []
        }
        
        # Add recommendations based on failures
        if any("OpenRouter" in issue for issue in self.issues_failed):
            report["recommendations"].append("Manually start OpenRouter API: python3 src/api/ai_router_api.py")
        
        if any("Vercel" in issue for issue in self.issues_failed):
            report["recommendations"].append("Use GitHub Pages deployment: ./admin-interface/deploy-gh-pages.sh")
        
        if any("Build" in issue for issue in self.issues_failed):
            report["recommendations"].append("Check build logs and fix dependencies")
        
        # Save report
        with open("production_fix_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_all_fixes(self):
        """Run all fixes in sequence"""
        self.log("🚀 Starting comprehensive production fixes...")
        
        # 1. Verify backend services
        self.verify_backend_services()
        
        # 2. Fix OpenRouter API
        self.fix_openrouter_api()
        
        # 3. Fix Vercel deployment
        self.fix_vercel_deployment()
        
        # 4. Set up GitHub Pages backup
        self.deploy_to_github_pages()
        
        # 5. Create monitoring
        self.create_monitoring_script()
        
        # 6. Generate report
        report = self.create_status_report()
        
        # Print summary
        self.log("📊 Fix Summary:")
        self.log(f"✅ Issues Fixed: {len(self.issues_fixed)}")
        for issue in self.issues_fixed:
            self.log(f"  ✅ {issue}")
        
        self.log(f"❌ Issues Failed: {len(self.issues_failed)}")
        for issue in self.issues_failed:
            self.log(f"  ❌ {issue}")
        
        if report["recommendations"]:
            self.log("💡 Recommendations:")
            for rec in report["recommendations"]:
                self.log(f"  💡 {rec}")
        
        return len(self.issues_failed) == 0

def main():
    fixer = ProductionFixer()
    success = fixer.run_all_fixes()
    
    if success:
        print("\n🎉 All production issues resolved!")
        sys.exit(0)
    else:
        print("\n⚠️ Some issues remain. Check production_fix_report.json for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 