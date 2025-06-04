#!/usr/bin/env python3
"""Deploy Cherry AI to cherry-ai.me"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return False
    print(f"✅ {description} completed")
    return True

def main():
    """Deploy Cherry AI to production"""
    print("🚀 Deploying Cherry AI to cherry-ai.me")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("docker-compose.prod.yml").exists():
        print("❌ Error: docker-compose.prod.yml not found. Are you in the right directory?")
        return 1
    
    # Step 1: Create production environment file
    print("\n📝 Creating production environment file...")
    env_prod = Path(".env.production")
    if not env_prod.exists():
        env_content = Path(".env").read_text()
        # Update for production
        env_content = env_content.replace("ENVIRONMENT=production", "ENVIRONMENT=production")
        env_content = env_content.replace("localhost", "cherry-ai.me")
        env_prod.write_text(env_content)
        print("✅ Created .env.production (please update API keys!)")
    else:
        print("✅ .env.production already exists")
    
    # Step 2: Build Docker images
    if not run_command(
        "docker-compose -f docker-compose.prod.yml build",
        "Building Docker images"
    ):
        return 1
    
    # Step 3: Start services
    if not run_command(
        "docker-compose -f docker-compose.prod.yml up -d",
        "Starting services"
    ):
        return 1
    
    # Step 4: Wait for services to be ready
    print("\n⏳ Waiting for services to be ready...")
    import time
    time.sleep(15)
    
    # Step 5: Run database migrations
    print("\n🗄️ Running database migrations...")
    migration_script = """
import asyncio
from sqlalchemy import text
from src.database import UnifiedDatabase

async def create_tables():
    db = UnifiedDatabase()
    
    # Create users table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create documents table for search
    await db.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500),
            content TEXT,
            search_vector tsvector,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for full-text search
    await db.execute('''
        CREATE INDEX IF NOT EXISTS idx_documents_search 
        ON documents USING GIN(search_vector)
    ''')
    
    await db.close()
    print("✅ Database tables created")

asyncio.run(create_tables())
"""
    
    migration_file = Path("temp_migration.py")
    migration_file.write_text(migration_script)
    
    if not run_command(
        f"docker-compose -f docker-compose.prod.yml exec -T api python /app/temp_migration.py",
        "Running migrations"
    ):
        # Try with venv
        run_command(
            f"./venv/bin/python temp_migration.py",
            "Running migrations (local)"
        )
    
    migration_file.unlink()
    
    # Step 6: Create admin user
    print("\n👤 Creating admin user...")
    create_admin_script = """
import asyncio
from src.auth.utils import create_admin_user

async def create_admin():
    result = await create_admin_user('scoobyjava', 'Huskers1983$', 'admin@cherry-ai.me')
    print(f"Admin user creation: {result}")

asyncio.run(create_admin())
"""
    
    admin_file = Path("temp_admin.py")
    admin_file.write_text(create_admin_script)
    
    run_command(
        f"docker-compose -f docker-compose.prod.yml exec -T api python /app/temp_admin.py",
        "Creating admin user"
    )
    
    admin_file.unlink()
    
    # Step 7: Setup Nginx
    print("\n🌐 Setting up Nginx...")
    nginx_config = Path("nginx-cherry-ai.conf")
    if nginx_config.exists():
        print("📋 Nginx configuration:")
        print(f"1. Copy to server: sudo cp {nginx_config} /etc/nginx/sites-available/cherry-ai.me")
        print("2. Enable site: sudo ln -sf /etc/nginx/sites-available/cherry-ai.me /etc/nginx/sites-enabled/")
        print("3. Test config: sudo nginx -t")
        print("4. Reload: sudo systemctl reload nginx")
    
    # Step 8: SSL Certificate
    print("\n🔒 SSL Certificate:")
    print("Run on server: sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me")
    
    # Final status
    print("\n" + "=" * 60)
    print("✅ Deployment complete!")
    print("\n📊 Service Status:")
    
    # Check services
    services = ["postgres", "redis", "weaviate", "api"]
    for service in services:
        result = subprocess.run(
            f"docker ps --filter name=cherry_ai_{service} --format '{{{{.Status}}}}'",
            shell=True, capture_output=True, text=True
        )
        status = result.stdout.strip() or "Not running"
        print(f"  {service}: {status}")
    
    print("\n🎉 Next steps:")
    print("1. Update .env.production with real API keys")
    print("2. Configure DNS to point cherry-ai.me to your server")
    print("3. Setup Nginx and SSL as shown above")
    print("4. Access https://cherry-ai.me")
    print("5. Login with: scoobyjava / Huskers1983$")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())