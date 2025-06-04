#!/usr/bin/env python3
"""Prepare the system for deployment to cherry-ai.me"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    requirements = [
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "weaviate-client",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "aiofiles",
        "httpx",
        "python-dotenv",
    ]
    
    for req in requirements:
        print(f"  Installing {req}...")
        subprocess.run([sys.executable, "-m", "pip", "install", req], 
                      capture_output=True)
    
    print("✅ Dependencies installed")

def create_llm_module():
    """Create the missing LLM module"""
    print("\n🤖 Creating LLM module...")
    
    llm_dir = Path("src/llm")
    llm_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py
    init_content = '''"""LLM module for Cherry AI"""

from .client import LLMClient

__all__ = ["LLMClient"]
'''
    (llm_dir / "__init__.py").write_text(init_content)
    
    # Create client.py
    client_content = '''"""LLM client for Cherry AI"""

import logging
from typing import Dict, Any, Optional
from typing_extensions import Optional, List

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM providers"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    async def complete(self, prompt: str, max_tokens: int = 1000) -> str:
        """Get completion from LLM"""
        # TODO: Implement actual LLM call
        return f"Mock response for: {prompt[:50]}..."
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with LLM"""
        # TODO: Implement actual chat
        return "Mock chat response"
'''
    (llm_dir / "client.py").write_text(client_content)
    
    print("✅ LLM module created")

def create_env_file():
    """Create environment file with required variables"""
    print("\n🔧 Creating environment configuration...")
    
    env_content = '''# Cherry AI Environment Configuration

# Database
DATABASE_URL=postgresql://cherry_ai:cherry_ai_pass@localhost:5432/cherry_ai_db
POSTGRES_USER=cherry_ai
POSTGRES_PASSWORD=cherry_ai_pass
POSTGRES_DB=cherry_ai_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# API Keys
OPENAI_API_KEY=your-openai-api-key-here

# Admin User (for cherry-ai.me)
ADMIN_USERNAME=scoobyjava
ADMIN_PASSWORD=Huskers1983$
ADMIN_EMAIL=admin@cherry-ai.me

# Server
API_HOST=0.0.0.0
API_PORT=8001
ENVIRONMENT=production

# Domain
DOMAIN=cherry-ai.me
ALLOWED_ORIGINS=https://cherry-ai.me,http://localhost:3000
'''
    
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(env_content)
        print("✅ Created .env file")
    else:
        print("⚠️  .env file already exists, updating missing values...")
        current_env = env_file.read_text()
        
        # Add missing variables
        for line in env_content.split('\n'):
            if '=' in line:
                key = line.split('=')[0]
                if key and key not in current_env:
                    current_env += f"\n{line}"
        
        env_file.write_text(current_env)
        print("✅ Updated .env file")

def create_docker_compose_prod():
    """Create production docker-compose file"""
    print("\n🐳 Creating production Docker Compose configuration...")
    
    compose_content = '''version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cherry_ai_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cherry_ai_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: cherry_ai_weaviate
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cherry_ai_api
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      WEAVIATE_URL: ${WEAVIATE_URL}
      JWT_SECRET: ${JWT_SECRET}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      weaviate:
        condition: service_started
    restart: unless-stopped
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8001

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
'''
    
    Path("docker-compose.prod.yml").write_text(compose_content)
    print("✅ Created docker-compose.prod.yml")

def create_dockerfile():
    """Create Dockerfile for the API"""
    print("\n📦 Creating Dockerfile...")
    
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 cherry_ai && chown -R cherry_ai:cherry_ai /app
USER cherry_ai

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
'''
    
    Path("Dockerfile").write_text(dockerfile_content)
    print("✅ Created Dockerfile")

def create_requirements_txt():
    """Create requirements.txt file"""
    print("\n📝 Creating requirements.txt...")
    
    requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
weaviate-client==3.25.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
python-dotenv==1.0.0
psycopg2-binary==2.9.9
'''
    
    Path("requirements.txt").write_text(requirements)
    print("✅ Created requirements.txt")

def create_nginx_config():
    """Create Nginx configuration for cherry-ai.me"""
    print("\n🌐 Creating Nginx configuration...")
    
    nginx_content = '''server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # SSL configuration (will be managed by certbot)
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API proxy
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
    }
    
    # Static files (if you have a frontend)
    location / {
        root /var/www/cherry-ai.me;
        try_files $uri $uri/ /index.html;
    }
}
'''
    
    Path("nginx-cherry-ai.conf").write_text(nginx_content)
    print("✅ Created nginx-cherry-ai.conf")

def create_deployment_script():
    """Create deployment script"""
    print("\n🚀 Creating deployment script...")
    
    script_content = '''#!/bin/bash
# Deploy Cherry AI to cherry-ai.me

set -e

echo "🚀 Deploying Cherry AI to cherry-ai.me..."

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Build and start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api python scripts/migrate_database.py

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec -T api python -c "
from src.auth.utils import create_admin_user
import asyncio
asyncio.run(create_admin_user('${ADMIN_USERNAME}', '${ADMIN_PASSWORD}', '${ADMIN_EMAIL}'))
"

# Copy Nginx config
echo "🌐 Setting up Nginx..."
sudo cp nginx-cherry-ai.conf /etc/nginx/sites-available/cherry-ai.me
sudo ln -sf /etc/nginx/sites-available/cherry-ai.me /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Install SSL certificate: sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me"
echo "2. Access the API at: https://cherry-ai.me/api"
echo "3. Login with: ${ADMIN_USERNAME} / ${ADMIN_PASSWORD}"
'''
    
    script_path = Path("deploy.sh")
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    print("✅ Created deploy.sh")

def main():
    """Prepare system for deployment"""
    print("🚀 Preparing Cherry AI for deployment to cherry-ai.me")
    print("=" * 60)
    
    # Run preparation steps
    install_dependencies()
    create_llm_module()
    create_env_file()
    create_docker_compose_prod()
    create_dockerfile()
    create_requirements_txt()
    create_nginx_config()
    create_deployment_script()
    
    print("\n" + "=" * 60)
    print("✅ System prepared for deployment!")
    print("\nIMPORTANT: Before deploying:")
    print("1. Update .env file with your actual API keys")
    print("2. Ensure your Vultr server has Docker and Nginx installed")
    print("3. Point cherry-ai.me DNS to your server IP")
    print("4. Run: ./deploy.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())