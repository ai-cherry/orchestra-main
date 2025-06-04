#!/usr/bin/env python3
"""Setup admin user with proper password hashing."""

import subprocess
import sys

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result

def main():
    print("=== Setting Up Admin User ===")
    
    # Create Python script to hash password and create user
    setup_script = """
import asyncio
import bcrypt
import asyncpg
import os

async def create_admin():
    # Hash the password
    password = "Huskers1983$"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Connect to database
    conn = await asyncpg.connect(
        host='cherry_ai_postgres',
        port=5432,
        user='postgres',
        password='postgres',
        database='cherry_ai'
    )
    
    try:
        # Create or update admin user
        await conn.execute('''
            INSERT INTO public.users (username, email, password_hash, is_admin)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (username) DO UPDATE
            SET email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                is_admin = EXCLUDED.is_admin
        ''', 'scoobyjava', 'admin@cherry-ai.me', password_hash, True)
        
        print("✓ Admin user created successfully!")
        print(f"  Username: scoobyjava")
        print(f"  Email: admin@cherry-ai.me")
        print(f"  Password: Huskers1983$")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        await conn.close()

asyncio.run(create_admin())
"""
    
    # Write script to file
    with open('/tmp/setup_admin.py', 'w') as f:
        f.write(setup_script)
    
    # Execute in container
    print("\nCreating admin user in database...")
    result = run_command("docker cp /tmp/setup_admin.py cherry_ai_api:/tmp/setup_admin.py")
    if result:
        result = run_command("docker exec cherry_ai_api python /tmp/setup_admin.py")
        if result and result.returncode == 0:
            print("\n✓ Admin user setup complete!")
        else:
            print("\n✗ Failed to create admin user")
            if result:
                print(f"Output: {result.stdout}")
                print(f"Error: {result.stderr}")
    
    # Test the API login endpoint
    print("\nTesting login endpoint...")
    test_cmd = '''curl -s -X POST http://localhost:8001/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username": "scoobyjava", "password": "Huskers1983$"}' '''
    
    result = run_command(test_cmd, check=False)
    if result and result.returncode == 0:
        print("✓ Login endpoint test:")
        print(result.stdout)
    else:
        print("✗ Login endpoint not responding as expected")

if __name__ == "__main__":
    main()