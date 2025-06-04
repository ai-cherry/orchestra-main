#!/usr/bin/env python3
"""
Setup secure environment variables for Cherry AI
"""

import os
import secrets
import string
from pathlib import Path

def generate_secure_key(length=32):
    """Generate a secure random key"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_env():
    """Generate secure environment configuration"""
    
    env_content = f"""# Cherry AI Environment Configuration
# Auto-generated secure configuration

# Security
SECRET_KEY={generate_secure_key(64)}
JWT_SECRET={generate_secure_key(64)}
ENCRYPTION_KEY={generate_secure_key(32)}

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cherry_ai
REDIS_URL=redis://localhost:6379/0

# API Keys (add your actual keys here)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
PORTKEY_API_KEY=your-portkey-key

# Authentication
PASSWORD_SALT={generate_secure_key(32)}
SESSION_SECRET={generate_secure_key(64)}
COOKIE_SECRET={generate_secure_key(32)}

# Services
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY={generate_secure_key(32)}

# Security Settings
CORS_ORIGINS=http://localhost:3000,https://cherry-ai.me
SECURE_COOKIES=true
SESSION_TIMEOUT=3600

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Additional Settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=localhost,cherry-ai.me
MAX_UPLOAD_SIZE=5242880
RATE_LIMIT_PER_MINUTE=60
"""
    
    # Backup existing .env if it exists
    env_path = Path(".env")
    if env_path.exists():
        backup_path = Path(".env.backup")
        env_path.rename(backup_path)
        print(f"✅ Backed up existing .env to .env.backup")
    
    # Write new .env
    with open(".env", "w") as f:
        f.write(env_content)
    
    # Set proper permissions
    os.chmod(".env", 0o600)
    
    print("✅ Generated secure .env file")
    print("⚠️  Remember to update the API keys with your actual values!")
    
    # Also create a production env file
    prod_env_content = f"""# Production Environment Variables
# Deploy this to your production server

# Security (use different values in production!)
SECRET_KEY={generate_secure_key(64)}
JWT_SECRET={generate_secure_key(64)}
ENCRYPTION_KEY={generate_secure_key(32)}

# Database (update with production values)
DATABASE_URL=postgresql://cherry_ai_user:secure_password@db.cherry-ai.me:5432/cherry_ai_prod
REDIS_URL=redis://:redis_password@redis.cherry-ai.me:6379/0

# Services
WEAVIATE_URL=http://weaviate.cherry-ai.me:8080
WEAVIATE_API_KEY={generate_secure_key(32)}

# Production Settings
CORS_ORIGINS=https://cherry-ai.me
SECURE_COOKIES=true
SESSION_TIMEOUT=3600
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=cherry-ai.me,api.cherry-ai.me
"""
    
    with open(".env.production", "w") as f:
        f.write(prod_env_content)
    os.chmod(".env.production", 0o600)
    
    print("✅ Generated .env.production template")

if __name__ == "__main__":
    generate_secure_env()