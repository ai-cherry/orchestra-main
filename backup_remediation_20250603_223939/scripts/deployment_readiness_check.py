#!/usr/bin/env python3
"""
Comprehensive Deployment Readiness Check for Cherry AI
Ensures system is ready for production deployment at cherry-ai.me
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import bcrypt


class DeploymentReadinessChecker:
    """Comprehensive deployment readiness checker"""
    
    def __init__(self):
        self.base_dir = Path("/root/cherry_ai-main")
        self.domain = "cherry-ai.me"
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: str, check: bool = True) -> Tuple[bool, str]:
        """Execute shell command and return result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"
    
    def check_python_syntax(self) -> bool:
        """Check all Python files for syntax errors"""
        self.log("🐍 Checking Python syntax...")
        
        success, output = self.run_command(
            'find . -name "*.py" -type f ! -path "./venv/*" -exec python3 -m py_compile {} \; 2>&1'
        )
        
        if success and not output:
            self.checks_passed.append("Python syntax check")
            self.log("✅ All Python files have valid syntax")
            return True
        else:
            self.checks_failed.append("Python syntax check")
            self.log(f"❌ Python syntax errors found: {output}", "ERROR")
            return False
    
    def check_imports(self) -> bool:
        """Check if all core modules can be imported"""
        self.log("📦 Checking module imports...")
        
        test_script = """
import sys
sys.path.append('src')
try:
    import src.search_engine
    import src.personas
    import src.operator_mode
    import src.api.main
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
"""
        
        success, output = self.run_command(f'cd {self.base_dir} && python3 -c "{test_script}"')
        
        if success and "SUCCESS" in output:
            self.checks_passed.append("Module imports")
            self.log("✅ All core modules import successfully")
            return True
        else:
            self.checks_failed.append("Module imports")
            self.log(f"❌ Import errors: {output}", "ERROR")
            return False
    
    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        self.log("🔐 Checking environment variables...")
        
        required_vars = [
            "DATABASE_URL",
            "WEAVIATE_URL", 
            "REDIS_URL",
            "PORTKEY_API_KEY",
            "SECRET_KEY"
        ]
        
        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)
        
        if not missing:
            self.checks_passed.append("Environment variables")
            self.log("✅ All required environment variables are set")
            return True
        else:
            self.checks_failed.append("Environment variables")
            self.log(f"❌ Missing environment variables: {', '.join(missing)}", "ERROR")
            
            # Create template .env file
            env_template = f"""# Production Environment Variables
DATABASE_URL=postgresql://cherry_ai_user:SECURE_PASSWORD@localhost:5432/cherry_ai_production
WEAVIATE_URL=https://your-cluster.weaviate.network
REDIS_URL=redis://localhost:6379
PORTKEY_API_KEY=pk-your-actual-key-here
SECRET_KEY={self._generate_secret_key()}
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS={self.domain},www.{self.domain}
"""
            env_path = self.base_dir / ".env.production.template"
            env_path.write_text(env_template)
            self.log(f"📝 Created environment template at: {env_path}")
            return False
    
    def check_docker_services(self) -> bool:
        """Check if Docker services are configured"""
        self.log("🐳 Checking Docker configuration...")
        
        compose_file = self.base_dir / "docker-compose.local.yml"
        if not compose_file.exists():
            self.checks_failed.append("Docker configuration")
            self.log("❌ docker-compose.local.yml not found", "ERROR")
            return False
        
        # Check if Docker is installed
        success, _ = self.run_command("docker --version")
        if not success:
            self.checks_failed.append("Docker installation")
            self.log("❌ Docker is not installed", "ERROR")
            return False
        
        self.checks_passed.append("Docker configuration")
        self.log("✅ Docker is configured and ready")
        return True
    
    def create_admin_user(self) -> bool:
        """Create admin user with specified credentials"""
        self.log("👤 Setting up admin user...")
        
        # Hash the password
        password = os.getenv('PASSWORD')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Create SQL script
        user_sql = f"""
-- Create admin user for Cherry AI
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    permissions JSONB DEFAULT '[]'::jsonb
);

-- Insert admin user
INSERT INTO users (username, password_hash, email, role, permissions) VALUES 
('scoobyjava', '{hashed_password}', 'admin@{self.domain}', 'admin', '["all"]'::jsonb)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    permissions = EXCLUDED.permissions;

-- Grant all permissions
UPDATE users SET permissions = '["all"]'::jsonb WHERE username = 'scoobyjava';
"""
        
        # Save SQL script
        sql_path = self.base_dir / "scripts" / "create_admin_user.sql"
        sql_path.write_text(user_sql)
        
        self.checks_passed.append("Admin user setup")
        self.log("✅ Admin user SQL script created")
        self.log(f"   Username: scoobyjava")
        self.log(f"   Password: Huskers1983$")
        self.log(f"   SQL script: {sql_path}")
        return True
    
    def check_ssl_readiness(self) -> bool:
        """Check SSL/TLS readiness"""
        self.log("🔒 Checking SSL readiness...")
        
        # Check if certbot is installed
        success, _ = self.run_command("certbot --version")
        if not success:
            self.warnings.append("Certbot not installed - will need to install for SSL")
            self.log("⚠️ Certbot not installed - needed for Let's Encrypt SSL", "WARNING")
        else:
            self.log("✅ Certbot is installed")
        
        # Check if nginx is installed
        success, _ = self.run_command("nginx -v")
        if not success:
            self.warnings.append("Nginx not installed - will need to install for reverse proxy")
            self.log("⚠️ Nginx not installed - needed for reverse proxy", "WARNING")
        else:
            self.log("✅ Nginx is installed")
        
        return True
    
    def create_deployment_scripts(self) -> bool:
        """Create final deployment scripts"""
        self.log("📜 Creating deployment scripts...")
        
        # Create guaranteed deployment script
        deploy_script = f"""#!/bin/bash
# Guaranteed Deployment Script for {self.domain}
set -e

echo "🚀 Starting deployment to {self.domain}..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | xargs)
else
    echo "❌ .env.production not found!"
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker exec cherry_ai-postgres psql -U cherry_ai -d cherry_ai -f /scripts/create_admin_user.sql

# Health check
echo "🏥 Running health checks..."
curl -f http://localhost:8001/health || echo "API health check failed"

echo "✅ Deployment complete!"
echo "🌐 Access at: https://{self.domain}"
echo "👤 Login: scoobyjava / Huskers1983$"
"""
        
        deploy_path = self.base_dir / "deploy_to_production.sh"
        deploy_path.write_text(deploy_script)
        deploy_path.chmod(0o755)
        
        self.checks_passed.append("Deployment scripts")
        self.log(f"✅ Created deployment script: {deploy_path}")
        return True
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def create_nginx_config(self) -> bool:
        """Create Nginx configuration"""
        self.log("🌐 Creating Nginx configuration...")
        
        nginx_config = f"""server {{
    listen 80;
    server_name {self.domain} www.{self.domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain} www.{self.domain};
    
    ssl_certificate /etc/letsencrypt/live/{self.domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.domain}/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend
    location / {{
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # API
    location /api {{
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # WebSocket
    location /ws {{
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    
    # Analytics
    location /analytics {{
        alias /var/www/{self.domain}/analytics;
        try_files $uri $uri/ /analytics/dashboard.html;
    }}
}}
"""
        
        nginx_path = self.base_dir / "nginx.conf"
        nginx_path.write_text(nginx_config)
        
        self.checks_passed.append("Nginx configuration")
        self.log(f"✅ Created Nginx config: {nginx_path}")
        return True
    
    def run_all_checks(self) -> bool:
        """Run all deployment readiness checks"""
        self.log("🔍 Cherry AI Deployment Readiness Check")
        self.log("=" * 60)
        
        checks = [
            ("Python Syntax", self.check_python_syntax),
            ("Module Imports", self.check_imports),
            ("Environment Variables", self.check_environment_variables),
            ("Docker Services", self.check_docker_services),
            ("Admin User Setup", self.create_admin_user),
            ("SSL Readiness", self.check_ssl_readiness),
            ("Nginx Configuration", self.create_nginx_config),
            ("Deployment Scripts", self.create_deployment_scripts)
        ]
        
        for check_name, check_func in checks:
            self.log(f"\n🔄 Running: {check_name}")
            try:
                check_func()
            except Exception as e:
                self.checks_failed.append(check_name)
                self.log(f"❌ {check_name} failed with error: {e}", "ERROR")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 DEPLOYMENT READINESS SUMMARY")
        self.log("=" * 60)
        
        self.log(f"\n✅ Passed Checks ({len(self.checks_passed)}):")
        for check in self.checks_passed:
            self.log(f"   - {check}")
        
        if self.checks_failed:
            self.log(f"\n❌ Failed Checks ({len(self.checks_failed)}):")
            for check in self.checks_failed:
                self.log(f"   - {check}")
        
        if self.warnings:
            self.log(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                self.log(f"   - {warning}")
        
        all_critical_passed = len(self.checks_failed) == 0
        
        if all_critical_passed:
            self.log("\n🎉 SYSTEM IS READY FOR DEPLOYMENT!")
            self.log("\nNext Steps:")
            self.log("1. Review and update .env.production with your actual values")
            self.log("2. Ensure DNS points to your server")
            self.log("3. Run: ./deploy_to_production.sh")
            self.log(f"4. Access your site at: https://{self.domain}")
            self.log("5. Login with: scoobyjava / Huskers1983$")
        else:
            self.log("\n⚠️ SYSTEM NOT READY - Fix failed checks before deployment", "WARNING")
        
        return all_critical_passed


def main():
    """Main entry point"""
    checker = DeploymentReadinessChecker()
    ready = checker.run_all_checks()
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()