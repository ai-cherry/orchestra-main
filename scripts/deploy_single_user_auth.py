#!/usr/bin/env python3
"""
Deploy and configure single-user authentication for Cherry AI
Integrates with existing infrastructure and updates all services
"""

import os
import sys
import subprocess
import json
import secrets
from pathlib import Path
from typing import Dict, Optional

class SingleUserAuthDeployment:
    def __init__(self):
        self.base_dir = Path("/root/cherry_ai-main")
        self.env_file = self.base_dir / ".env"
        self.api_key = None
        self.context = os.getenv("cherry_ai_CONTEXT", "development")
        
    def run(self):
        """Execute deployment steps"""
        print("🔐 Deploying Single-User Authentication System")
        print("=" * 60)
        
        try:
            # Step 1: Generate or retrieve API key
            self.setup_api_key()
            
            # Step 2: Update environment configuration
            self.update_environment()
            
            # Step 3: Update Docker configuration
            self.update_docker_config()
            
            # Step 4: Deploy authentication services
            self.deploy_auth_services()
            
            # Step 5: Run tests
            self.run_tests()
            
            # Step 6: Show deployment summary
            self.show_summary()
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            sys.exit(1)
    
    def setup_api_key(self):
        """Generate or retrieve API key"""
        print("\n🔑 Setting up API key...")
        
        # Check if API key already exists
        if os.getenv("cherry_ai_API_KEY"):
            self.api_key = os.getenv("cherry_ai_API_KEY")
            print("  ✓ Using existing API key from environment")
            return
        
        # Check .env file
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
if line.startswith("cherry_ai_API_KEY = os.getenv('ORCHESTRA_SCRIPT_API_KEY')
                        key = line.split("=", 1)[1].strip()
                        if key and key != "your-api-key":
                            self.api_key = key
                            print("  ✓ Using existing API key from .env")
                            return
        
        # Generate new API key
        self.api_key = secrets.token_urlsafe(48)
        print(f"  ✓ Generated new API key: {self.api_key[:10]}...")
    
    def update_environment(self):
        """Update environment configuration"""
        print("\n📝 Updating environment configuration...")
        
        # Read existing .env
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
        
        # Update with single-user auth settings
        env_vars.update({
            "cherry_ai_API_KEY": self.api_key,
            "cherry_ai_CONTEXT": self.context,
            "AUTH_MODE": "single_user",
            "ENABLE_RBAC": "context_based",
            "RATE_LIMIT_ENABLED": "true" if self.context != "development" else "false"
        })
        
        # Write updated .env
        with open(self.env_file, 'w') as f:
            f.write("# Cherry AI Single-User Configuration\n")
            f.write("# Auto-generated - DO NOT COMMIT WITH SECRETS\n\n")
            
            # Group by category
            categories = {
                "Authentication": ["cherry_ai_API_KEY", "AUTH_MODE", "ENABLE_RBAC"],
                "Context": ["cherry_ai_CONTEXT", "RATE_LIMIT_ENABLED"],
                "Services": ["API_", "MCP_", "WEAVIATE_"],
                "Monitoring": ["GRAFANA_", "PROMETHEUS_", "LOG_"],
                "Other": []
            }
            
            written_keys = set()
            
            for category, prefixes in categories.items():
                matching_vars = {}
                
                if category == "Authentication" or category == "Context":
                    # Special handling for auth vars
                    for key in prefixes:
                        if key in env_vars:
                            matching_vars[key] = env_vars[key]
                            written_keys.add(key)
                else:
                    # Prefix matching for other categories
                    for key, value in env_vars.items():
                        if any(key.startswith(prefix) for prefix in prefixes):
                            matching_vars[key] = value
                            written_keys.add(key)
                
                if matching_vars:
                    f.write(f"\n# {category}\n")
                    for key, value in sorted(matching_vars.items()):
                        f.write(f"{key}={value}\n")
            
            # Write remaining vars
            remaining = {k: v for k, v in env_vars.items() if k not in written_keys}
            if remaining:
                f.write("\n# Other\n")
                for key, value in sorted(remaining.items()):
                    f.write(f"{key}={value}\n")
        
        print("  ✓ Environment configuration updated")
    
    def update_docker_config(self):
        """Update Docker configuration for single-user auth"""
        print("\n🐳 Updating Docker configuration...")
        
        # Create docker-compose override for auth
        override_config = {
            "version": "3.8",
            "services": {
                "api": {
                    "environment": [
                        "cherry_ai_API_KEY=${cherry_ai_API_KEY}",
                        "cherry_ai_CONTEXT=${cherry_ai_CONTEXT}",
                        "AUTH_MODE=single_user"
                    ],
                    "volumes": [
                        "./mcp_server:/app/mcp_server:ro"
                    ]
                },
                "nginx": {
                    "environment": [
                        "API_KEY_HEADER=X-API-Key"
                    ]
                }
            }
        }
        
        override_file = self.base_dir / "docker-compose.auth.yml"
        with open(override_file, 'w') as f:
            import yaml
            yaml.dump(override_config, f, default_flow_style=False)
        
        print("  ✓ Created docker-compose.auth.yml")
        
        # Update nginx configuration
        self.create_nginx_config()
    
    def create_nginx_config(self):
        """Create nginx configuration for single-user auth"""
        nginx_config = """
# Cherry AI Nginx Configuration - Single User
upstream api {
    server api:8000;
}

# Rate limiting zones (only in production)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=burst_limit:10m rate=20r/s;

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Health check (no auth)
    location /health {
        proxy_pass http://api/health;
        access_log off;
    }
    
    # API endpoints
    location /api/ {
        # Pass API key header
        proxy_set_header X-API-Key $http_x_api_key;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Rate limiting (except in development)
        set $limit_rate 0;
        if ($cherry_ai_context != "development") {
            limit_req zone=api_limit burst=20 nodelay;
            limit_req zone=burst_limit burst=50 nodelay;
        }
        
        proxy_pass http://api;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ =404;
    }
}
"""
        
        nginx_dir = self.base_dir / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        
        with open(nginx_dir / "nginx.conf", 'w') as f:
            f.write(nginx_config)
        
        print("  ✓ Created nginx configuration")
    
    def deploy_auth_services(self):
        """Deploy authentication services"""
        print("\n🚀 Deploying authentication services...")
        
        # Stop existing services
        print("  - Stopping existing services...")
        subprocess.run(
            ["docker-compose", "down"],
            cwd=self.base_dir,
            capture_output=True
        )
        
        # Start services with auth configuration
        print("  - Starting services with authentication...")
        cmd = [
            "docker-compose",
            "-f", "docker-compose.yml",
            "-f", "docker-compose.auth.yml",
            "up", "-d"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ❌ Failed to start services: {result.stderr}")
            sys.exit(1)
        
        print("  ✓ Services started with authentication")
        
        # Wait for services to be ready
        print("  - Waiting for services to be ready...")
        import time
        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(10)
    
    def run_tests(self):
        """Run authentication tests"""
        print("\n🧪 Running authentication tests...")
        
        test_script = self.base_dir / "scripts" / "test_single_user_auth.py"
        self.create_test_script(test_script)
        
        # Make executable and run
        test_script.chmod(0o755)
        result = subprocess.run(
            [sys.executable, str(test_script)],
            env={**os.environ, "cherry_ai_API_KEY": self.api_key},
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ All authentication tests passed")
        else:
            print(f"  ❌ Tests failed: {result.stdout}")
    
    def create_test_script(self, path: Path):
        """Create authentication test script"""
        test_content = f'''#!/usr/bin/env python3
"""Test single-user authentication"""

import requests
import os
import sys

API_URL = "http://localhost:8000"
API_KEY = os.getenv("cherry_ai_API_KEY")

def test_no_auth():
    """Test request without authentication"""
    response = requests.get(f"{{API_URL}}/api/v1/info")
    assert response.status_code == 401, f"Expected 401, got {{response.status_code}}"
    print("✓ No auth test passed")

def test_with_auth():
    """Test request with authentication"""
    headers = {{"X-API-Key": API_KEY}}
    response = requests.get(f"{{API_URL}}/api/v1/info", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {{response.status_code}}"
    data = response.json()
    assert "context" in data
    assert "permissions" in data
    print("✓ Auth test passed")

def test_invalid_auth():
    """Test request with invalid authentication"""
    headers = {{"X-API-Key": "invalid-key"}}
    response = requests.get(f"{{API_URL}}/api/v1/info", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {{response.status_code}}"
    print("✓ Invalid auth test passed")

def test_health_no_auth():
    """Test health endpoint requires no auth"""
    response = requests.get(f"{{API_URL}}/health")
    assert response.status_code == 200, f"Expected 200, got {{response.status_code}}"
    print("✓ Health check test passed")

if __name__ == "__main__":
    try:
        test_no_auth()
        test_with_auth()
        test_invalid_auth()
        test_health_no_auth()
        print("\\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\\n❌ Test failed: {{e}}")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error: {{e}}")
        sys.exit(1)
'''
        
        with open(path, 'w') as f:
            f.write(test_content)
    
    def show_summary(self):
        """Show deployment summary"""
        print("\n" + "=" * 60)
        print("✅ SINGLE-USER AUTHENTICATION DEPLOYED")
        print("=" * 60)
        
        print(f"\n🔑 API Key: {self.api_key[:20]}...")
        print(f"🌍 Context: {self.context}")
        
        print("\n📍 Endpoints:")
        print("  - API: http://localhost:8000")
        print("  - Health: http://localhost:8000/health (no auth)")
        
        print("\n🔒 Authentication:")
        print("  - Header: X-API-Key")
        print("  - Mode: Single-user with context-based permissions")
        
        print("\n💡 Usage Examples:")
        print("  # Test authentication")
        print(f'  curl -H "X-API-Key: {self.api_key}" http://localhost:8000/api/v1/info')
        
        print("\n  # Create workflow")
        print(f'  curl -X POST -H "X-API-Key: {self.api_key}" \\')
        print('       -H "Content-Type: application/json" \\')
        print('       -d \'{"name": "test-workflow"}\' \\')
        print('       http://localhost:8000/api/v1/workflows')
        
        print("\n📝 Configuration:")
        print(f"  - Environment: {self.env_file}")
        print("  - Docker: docker-compose.auth.yml")
        print("  - Nginx: nginx/nginx.conf")

if __name__ == "__main__":
    deployment = SingleUserAuthDeployment()
    deployment.run()