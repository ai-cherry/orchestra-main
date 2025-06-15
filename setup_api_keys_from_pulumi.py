#!/usr/bin/env python3
"""
Orchestra AI - Fetch API Keys from Pulumi and Configure Environment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def run_pulumi_command(cmd):
    """Run a Pulumi command and return output"""
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd='pulumi'
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception running command: {e}")
        return None

def get_pulumi_secrets():
    """Fetch all secrets from Pulumi config"""
    secrets = {}
    
    # List of secrets we need for Phase 1
    required_secrets = [
        'openrouter_api_key',
        'openai_api_key',
        'pinecone_api_key',
        'exa_ai_api_key',
        'serp_api_key',
        'venice_ai_api_key',
        'apify_api_key',
        'zenrows_api_key',
        'redis_url',
        'database_url',
        'github_token',
        'vercel_token',
        'lambda_api_key',
        'portkey_api_key',
        'anthropic_api_key'
    ]
    
    print("🔑 Fetching secrets from Pulumi...")
    
    for secret in required_secrets:
        # Try to get the secret
        value = run_pulumi_command(f"pulumi config get {secret}")
        if value:
            secrets[secret.upper()] = value
            print(f"  ✅ Found {secret}")
        else:
            # Try without underscore (e.g., 'openrouterapi' instead of 'openrouter_api')
            alt_secret = secret.replace('_', '')
            value = run_pulumi_command(f"pulumi config get {alt_secret}")
            if value:
                secrets[secret.upper()] = value
                print(f"  ✅ Found {secret} (as {alt_secret})")
            else:
                print(f"  ⚠️  Missing {secret}")
    
    return secrets

def update_env_file(secrets):
    """Update .env file with secrets"""
    env_path = Path('.env')
    
    # Read existing .env if it exists
    existing_env = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_env[key] = value
    
    # Merge with new secrets
    existing_env.update(secrets)
    
    # Add additional required environment variables
    existing_env.update({
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'PINECONE_ENVIRONMENT': 'us-west-2',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1',
        'API_HOST': '0.0.0.0',
        'API_PORT': '5000',
        'MCP_PORT': '8003'
    })
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.write("# Orchestra AI Environment Configuration\n")
        f.write("# Auto-generated from Pulumi secrets\n\n")
        
        # Group by category
        categories = {
            'LLM Configuration': ['OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'PORTKEY_API_KEY'],
            'Search APIs': ['EXA_AI_API_KEY', 'SERP_API_KEY', 'VENICE_AI_API_KEY', 'APIFY_API_KEY', 'ZENROWS_API_KEY'],
            'Infrastructure': ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'DATABASE_URL', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT'],
            'Deployment': ['GITHUB_TOKEN', 'VERCEL_TOKEN', 'LAMBDA_API_KEY'],
            'Flask Configuration': ['FLASK_ENV', 'FLASK_DEBUG', 'API_HOST', 'API_PORT', 'MCP_PORT']
        }
        
        for category, keys in categories.items():
            f.write(f"# {category}\n")
            for key in keys:
                if key in existing_env:
                    f.write(f"{key}={existing_env[key]}\n")
            f.write("\n")
        
        # Write any remaining keys
        f.write("# Other Configuration\n")
        for key, value in existing_env.items():
            if not any(key in keys for keys in categories.values()):
                f.write(f"{key}={value}\n")
    
    print(f"\n✅ Updated .env file with {len(secrets)} secrets")

def fix_mcp_servers():
    """Fix MCP server import issues"""
    print("\n🔧 Fixing MCP server issues...")
    
    # Create a simple memory_management_server.py stub
    mcp_content = '''"""
Orchestra AI - Memory Management MCP Server (Stub)
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoryManagementServer:
    """Stub MCP server for memory management"""
    
    def __init__(self, port: int = 8003):
        self.port = port
        logger.info(f"Memory Management MCP Server initialized on port {port}")
    
    async def start(self):
        """Start the server"""
        logger.info("Memory Management MCP Server started (stub mode)")
        # Keep running
        while True:
            await asyncio.sleep(60)

# ASGI app for uvicorn
app = MemoryManagementServer()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("memory_management_server:app", host="0.0.0.0", port=8003, reload=True)
'''
    
    with open('memory_management_server.py', 'w') as f:
        f.write(mcp_content)
    
    print("  ✅ Created memory_management_server.py stub")
    
    # Install mcp package
    print("  📦 Installing mcp package...")
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp"], check=False)

def update_main_app():
    """Update main Flask app to include new routes"""
    print("\n🔄 Updating main Flask app...")
    
    main_py_path = Path('src/main.py')
    if not main_py_path.exists():
        main_py_path = Path('main.py')
    
    if main_py_path.exists():
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Check if chat_v2 is already imported
        if 'chat_v2' not in content:
            # Add import
            import_line = "from src.routes.chat_v2 import chat_v2_bp"
            register_line = "app.register_blueprint(chat_v2_bp)"
            
            # Find where to insert
            lines = content.split('\n')
            new_lines = []
            import_added = False
            register_added = False
            
            for line in lines:
                # Add import after other route imports
                if not import_added and 'from src.routes' in line:
                    new_lines.append(line)
                    new_lines.append(import_line)
                    import_added = True
                # Add registration after other blueprint registrations
                elif not register_added and 'app.register_blueprint' in line:
                    new_lines.append(line)
                    new_lines.append(f"    {register_line}")
                    register_added = True
                else:
                    new_lines.append(line)
            
            # Write back
            with open(main_py_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            print("  ✅ Updated main.py with chat_v2 routes")
        else:
            print("  ✅ chat_v2 routes already registered")
    else:
        print("  ⚠️  Could not find main.py")

def main():
    """Main setup function"""
    print("🚀 Orchestra AI API Key Setup from Pulumi\n")
    
    # 1. Fetch secrets from Pulumi
    secrets = get_pulumi_secrets()
    
    if not secrets:
        print("\n❌ No secrets found. Make sure you're logged into Pulumi and have the correct stack selected.")
        print("Run: cd pulumi && pulumi stack select production")
        return
    
    # 2. Update .env file
    update_env_file(secrets)
    
    # 3. Fix MCP servers
    fix_mcp_servers()
    
    # 4. Update main app
    update_main_app()
    
    print("\n✅ Setup complete! Next steps:")
    print("1. Review the .env file to ensure all keys are present")
    print("2. Start Redis: redis-server")
    print("3. Run the Flask app: python src/main.py")
    print("4. Test the new chat v2 endpoint")

if __name__ == "__main__":
    main() 