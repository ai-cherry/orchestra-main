#!/usr/bin/env python3
"""Verify Cherry AI deployment with proper MCP, persona, and infrastructure alignment."""

import subprocess
import json
import sys
import time
import os

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result

def check_mcp_servers():
    """Verify MCP server connections."""
    print("\n=== Checking MCP Server Connections ===")
    
    mcp_servers = {
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "service": "PostgreSQL for data persistence"
        },
        "weaviate": {
            "host": "localhost", 
            "port": 8081,
            "service": "Weaviate for vector storage"
        },
        "airbyte": {
            "host": "localhost",
            "port": 8000,
            "service": "Airbyte for data integration"
        },
        "vultr": {
            "service": "Vultr cloud infrastructure",
            "api_endpoint": "https://api.vultr.com/v2/"
        }
    }
    
    for server, config in mcp_servers.items():
        print(f"\n{server.upper()}:")
        if "port" in config:
            result = run_command(f"nc -zv {config['host']} {config['port']}", check=False)
            if result and result.returncode == 0:
                print(f"✓ {config['service']} is accessible on port {config['port']}")
            else:
                print(f"✗ {config['service']} is NOT accessible on port {config['port']}")
        else:
            print(f"  {config['service']} - API-based connection")

def check_personas():
    """Verify persona configurations."""
    print("\n=== Checking Persona Configurations ===")
    
    personas = {
        "Cherry": {
            "domain": "Personal",
            "description": "Personal AI assistant",
            "database_schema": "personal",
            "weaviate_class": "PersonalMemory"
        },
        "Sophia": {
            "domain": "PayReady",
            "description": "Financial services AI",
            "database_schema": "payready",
            "weaviate_class": "PayReadyMemory"
        },
        "Karen": {
            "domain": "ParagonRX",
            "description": "Healthcare AI assistant",
            "database_schema": "paragonrx",
            "weaviate_class": "ParagonRXMemory"
        }
    }
    
    # Check database schemas
    for persona, config in personas.items():
        print(f"\n{persona} ({config['domain']}):")
        print(f"  Description: {config['description']}")
        
        # Check if schema exists in PostgreSQL
        result = run_command(
            f"docker exec cherry_ai_postgres psql -U postgres -d cherry_ai -c "
            f"\"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{config['database_schema']}';\"",
            check=False
        )
        if result and config['database_schema'] in result.stdout:
            print(f"  ✓ Database schema '{config['database_schema']}' exists")
        else:
            print(f"  ✗ Database schema '{config['database_schema']}' NOT found")
            # Create schema
            run_command(
                f"docker exec cherry_ai_postgres psql -U postgres -d cherry_ai -c "
                f"\"CREATE SCHEMA IF NOT EXISTS {config['database_schema']};\"",
                check=False
            )
            print(f"  → Created schema '{config['database_schema']}'")

def check_infrastructure():
    """Verify infrastructure components."""
    print("\n=== Checking Infrastructure Components ===")
    
    # Check Docker containers
    print("\nDocker Containers:")
    result = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    if result:
        print(result.stdout)
    
    # Check API health
    print("\nAPI Health Check:")
    result = run_command("curl -s http://localhost:8001/health", check=False)
    if result and result.returncode == 0:
        print(f"✓ API is healthy: {result.stdout}")
    else:
        print("✗ API health check failed")
    
    # Check Nginx
    print("\nNginx Status:")
    result = run_command("sudo systemctl status nginx --no-pager", check=False)
    if result and "active (running)" in result.stdout:
        print("✓ Nginx is running")
    else:
        print("✗ Nginx is not running properly")
    
    # Check SSL certificate
    print("\nSSL Certificate:")
    result = run_command("sudo certbot certificates", check=False)
    if result and "cherry-ai.me" in result.stdout:
        print("✓ SSL certificate is valid for cherry-ai.me")
    else:
        print("✗ SSL certificate issue detected")

def setup_database_structure():
    """Setup proper database structure for all components."""
    print("\n=== Setting Up Database Structure ===")
    
    # Create PostgreSQL user if not exists
    print("\nCreating database user...")
    commands = [
        "CREATE USER IF NOT EXISTS postgres WITH SUPERUSER PASSWORD 'postgres';",
        "ALTER DATABASE cherry_ai OWNER TO postgres;",
        "GRANT ALL PRIVILEGES ON DATABASE cherry_ai TO postgres;"
    ]
    
    for cmd in commands:
        run_command(
            f'docker exec cherry_ai_postgres psql -U postgres -c "{cmd}"',
            check=False
        )
    
    # Create tables for each persona
    print("\nCreating persona tables...")
    personas_sql = """
    -- Create schemas for each domain
    CREATE SCHEMA IF NOT EXISTS personal;
    CREATE SCHEMA IF NOT EXISTS payready;
    CREATE SCHEMA IF NOT EXISTS paragonrx;
    
    -- Create users table in public schema
    CREATE TABLE IF NOT EXISTS public.users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create memory tables for each persona
    CREATE TABLE IF NOT EXISTS personal.memories (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES public.users(id),
        content TEXT,
        embedding VECTOR(1536),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS payready.memories (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES public.users(id),
        content TEXT,
        embedding VECTOR(1536),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS paragonrx.memories (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES public.users(id),
        content TEXT,
        embedding VECTOR(1536),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Write SQL to file and execute
    with open('/tmp/setup_personas.sql', 'w') as f:
        f.write(personas_sql)
    
    result = run_command(
        "docker exec -i cherry_ai_postgres psql -U postgres -d cherry_ai < /tmp/setup_personas.sql",
        check=False
    )
    if result and result.returncode == 0:
        print("✓ Database structure created successfully")
    else:
        print("✗ Error creating database structure")

def create_admin_user():
    """Create admin user with proper credentials."""
    print("\n=== Creating Admin User ===")
    
    admin_sql = """
    INSERT INTO public.users (username, email, password_hash, is_admin)
    VALUES ('scoobyjava', 'admin@cherry-ai.me', '$2b$12$dummy_hash_for_now', true)
    ON CONFLICT (username) DO UPDATE
    SET email = EXCLUDED.email,
        is_admin = EXCLUDED.is_admin;
    """
    
    result = run_command(
        f'docker exec cherry_ai_postgres psql -U postgres -d cherry_ai -c "{admin_sql}"',
        check=False
    )
    if result and result.returncode == 0:
        print("✓ Admin user created/updated")
    else:
        print("✗ Error creating admin user")

def update_api_configuration():
    """Update API configuration for proper connections."""
    print("\n=== Updating API Configuration ===")
    
    env_content = """
DATABASE_URL=postgresql://postgres:postgres@cherry_ai_postgres:5432/cherry_ai
WEAVIATE_URL=http://cherry_ai_weaviate:8080
REDIS_URL=redis://cherry_ai_redis:6379
JWT_SECRET=your-secret-key-here
VULTR_API_KEY=${VULTR_API_KEY}
AIRBYTE_API_URL=http://localhost:8000
"""
    
    # Write environment file
    with open('/tmp/api.env', 'w') as f:
        f.write(env_content)
    
    # Copy to container
    run_command("docker cp /tmp/api.env cherry_ai_api:/app/.env", check=False)
    
    # Restart API container
    print("\nRestarting API container...")
    run_command("docker restart cherry_ai_api", check=False)
    # TODO: Replace with asyncio.sleep() for async code
    time.sleep(5)
    
    # Check if API is back up
    result = run_command("curl -s http://localhost:8001/health", check=False)
    if result and result.returncode == 0:
        print("✓ API restarted successfully")
    else:
        print("✗ API failed to restart")

def main():
    print("=== Cherry AI Deployment Verification ===")
    print("Ensuring alignment with MCP servers, personas, and infrastructure")
    
    # Run all checks
    check_mcp_servers()
    check_infrastructure()
    setup_database_structure()
    check_personas()
    create_admin_user()
    update_api_configuration()
    
    print("\n=== Deployment Summary ===")
    print("1. Website: https://cherry-ai.me")
    print("2. Login: scoobyjava / Huskers1983$")
    print("3. MCP Servers:")
    print("   - PostgreSQL: Port 5432 (Data persistence)")
    print("   - Weaviate: Port 8081 (Vector storage)")
    print("   - Airbyte: Port 8000 (Data integration)")
    print("   - Vultr: Cloud infrastructure")
    print("4. Personas:")
    print("   - Cherry (Personal domain)")
    print("   - Sophia (PayReady domain)")
    print("   - Karen (ParagonRX domain)")
    print("\nNote: The admin password needs to be properly hashed. Use the web interface to set it.")

if __name__ == "__main__":
    main()