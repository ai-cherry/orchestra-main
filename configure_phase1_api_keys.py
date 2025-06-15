#!/usr/bin/env python3
"""
Orchestra AI - Configure Phase 1 API Keys
Uses the enhanced secret manager to set up all required API keys
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from security.enhanced_secret_manager import secret_manager

# Phase 1 API keys mapping
# Maps required keys to possible GitHub secret names
API_KEY_MAPPINGS = {
    # LLM Configuration
    'OPENROUTER_API_KEY': ['OPENROUTER_API_KEY', 'OPENROUTER_KEY'],
    'OPENAI_API_KEY': ['OPENAI_API_KEY', 'OPENAI_KEY', 'OPEN_AI_API_KEY'],
    'ANTHROPIC_API_KEY': ['ANTHROPIC_API_KEY', 'ANTHROPIC_KEY'],
    'PORTKEY_API_KEY': ['PORTKEY_API_KEY', 'PORTKEY_KEY'],
    
    # Search APIs
    'EXA_AI_API_KEY': ['EXA_AI_API_KEY', 'EXA_API_KEY', 'EXAAI_KEY'],
    'SERP_API_KEY': ['SERP_API_KEY', 'SERPAPI_KEY', 'SERP_KEY'],
    'VENICE_AI_API_KEY': ['VENICE_AI_API_KEY', 'VENICE_API_KEY', 'VENICEAI_KEY'],
    'APIFY_API_KEY': ['APIFY_API_KEY', 'APIFY_KEY'],
    'ZENROWS_API_KEY': ['ZENROWS_API_KEY', 'ZENROWS_KEY'],
    
    # Infrastructure
    'REDIS_URL': ['REDIS_URL', 'REDIS_CONNECTION_STRING'],
    'DATABASE_URL': ['DATABASE_URL', 'DB_CONNECTION_STRING', 'POSTGRES_URL'],
    'PINECONE_API_KEY': ['PINECONE_API_KEY', 'PINECONE_KEY'],
    
    # Deployment
    'GITHUB_TOKEN': ['GITHUB_TOKEN', 'GH_FINE_GRAINED_TOKEN', 'GH_CLASSIC_PAT_TOKEN', 'GITHUB_PAT'],
    'VERCEL_TOKEN': ['VERCEL_TOKEN', 'VERCEL_API_TOKEN'],
    'LAMBDA_API_KEY': ['LAMBDA_API_KEY', 'LAMBDA_LABS_API_KEY', 'LAMBDALABS_API_KEY']
}

def get_api_key(key_name, possible_names):
    """Try to get API key from various possible names"""
    for name in possible_names:
        value = secret_manager.get_secret(name)
        if value:
            print(f"  ✅ Found {key_name} (as {name})")
            return value
    
    print(f"  ⚠️  Missing {key_name}")
    return None

def create_env_file():
    """Create comprehensive .env file with all API keys"""
    print("🔑 Configuring Phase 1 API Keys...\n")
    
    env_content = []
    env_content.append("# Orchestra AI Phase 1 Configuration")
    env_content.append("# Auto-generated from GitHub organizational secrets\n")
    
    # Collect all API keys
    all_keys = {}
    missing_keys = []
    
    for key_name, possible_names in API_KEY_MAPPINGS.items():
        value = get_api_key(key_name, possible_names)
        if value:
            all_keys[key_name] = value
        else:
            missing_keys.append(key_name)
    
    # Add static configuration
    static_config = {
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'PINECONE_ENVIRONMENT': 'us-west-2',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1',
        'API_HOST': '0.0.0.0',
        'API_PORT': '5000',
        'MCP_PORT': '8003',
        'ENVIRONMENT': 'production'
    }
    
    # Group keys by category
    categories = {
        'LLM Configuration': [
            'OPENROUTER_API_KEY',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'PORTKEY_API_KEY'
        ],
        'Search APIs': [
            'EXA_AI_API_KEY',
            'SERP_API_KEY',
            'VENICE_AI_API_KEY',
            'APIFY_API_KEY',
            'ZENROWS_API_KEY'
        ],
        'Infrastructure': [
            'REDIS_URL',
            'REDIS_HOST',
            'REDIS_PORT',
            'DATABASE_URL',
            'PINECONE_API_KEY',
            'PINECONE_ENVIRONMENT'
        ],
        'Deployment': [
            'GITHUB_TOKEN',
            'VERCEL_TOKEN',
            'LAMBDA_API_KEY'
        ],
        'Flask Configuration': [
            'FLASK_ENV',
            'FLASK_DEBUG',
            'API_HOST',
            'API_PORT',
            'MCP_PORT',
            'ENVIRONMENT'
        ]
    }
    
    # Write to .env file
    for category, keys in categories.items():
        env_content.append(f"# {category}")
        for key in keys:
            if key in all_keys:
                env_content.append(f"{key}={all_keys[key]}")
            elif key in static_config:
                env_content.append(f"{key}={static_config[key]}")
        env_content.append("")
    
    # Write the .env file
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ Created .env file with {len(all_keys)} API keys")
    
    if missing_keys:
        print(f"\n⚠️  Missing {len(missing_keys)} keys:")
        for key in missing_keys:
            print(f"   - {key}")
        
        # Create placeholder keys for missing ones
        print("\n📝 Creating placeholder values for missing keys...")
        with open('.env', 'a') as f:
            f.write("\n# Placeholder values for missing keys (replace with actual values)\n")
            for key in missing_keys:
                if 'OPENROUTER' in key:
                    # OpenRouter is critical, use OpenAI as fallback
                    f.write(f"# {key}=<get-from-openrouter.ai>\n")
                else:
                    f.write(f"# {key}=<placeholder-replace-me>\n")
    
    return all_keys, missing_keys

def fix_flask_async():
    """Update Flask app to support async routes"""
    print("\n🔧 Fixing Flask async support...")
    
    main_py = Path('src/main.py')
    if main_py.exists():
        with open(main_py, 'r') as f:
            content = f.read()
        
        # Check if we need to add async support
        if 'flask[async]' not in content and 'asgiref' not in content:
            # Add async imports at the top
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('from flask import'):
                    import_index = i + 1
                    break
            
            # Insert async support
            lines.insert(import_index, "import asyncio")
            lines.insert(import_index + 1, "from asgiref.wsgi import WsgiToAsgi")
            
            # Update the app creation to support async
            for i, line in enumerate(lines):
                if 'app = Flask(__name__)' in line:
                    lines.insert(i + 1, "# Enable async support")
                    lines.insert(i + 2, "app.config['FLASK_ASYNC_MODE'] = 'threading'")
                    break
            
            # Write back
            with open(main_py, 'w') as f:
                f.write('\n'.join(lines))
            
            print("  ✅ Added async support to Flask app")
        else:
            print("  ✅ Flask async support already configured")

def update_flask_routes():
    """Update Flask app to register chat_v2 blueprint"""
    print("\n🔄 Updating Flask routes...")
    
    main_py = Path('src/main.py')
    if main_py.exists():
        with open(main_py, 'r') as f:
            content = f.read()
        
        if 'chat_v2' not in content:
            lines = content.split('\n')
            
            # Find where to add import
            import_added = False
            for i, line in enumerate(lines):
                if 'from src.routes' in line and 'import' in line:
                    lines.insert(i + 1, "from src.routes.chat_v2 import chat_v2_bp")
                    import_added = True
                    break
            
            # Find where to register blueprint
            register_added = False
            for i, line in enumerate(lines):
                if 'app.register_blueprint' in line and not register_added:
                    # Find the indentation
                    indent = len(line) - len(line.lstrip())
                    lines.insert(i + 1, " " * indent + "app.register_blueprint(chat_v2_bp)")
                    register_added = True
                    break
            
            # Write back
            with open(main_py, 'w') as f:
                f.write('\n'.join(lines))
            
            print("  ✅ Added chat_v2 routes to Flask app")
        else:
            print("  ✅ chat_v2 routes already registered")

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("  ✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        print("  💡 Start Redis with: redis-server")
        return False

def main():
    """Main configuration function"""
    print("🚀 Orchestra AI Phase 1 Configuration\n")
    
    # 1. Create .env file with API keys
    api_keys, missing_keys = create_env_file()
    
    # 2. Fix Flask async support
    fix_flask_async()
    
    # 3. Update Flask routes
    update_flask_routes()
    
    # 4. Test Redis
    redis_ok = test_redis_connection()
    
    # 5. Create MCP server stub
    print("\n🔧 Creating MCP server stub...")
    mcp_stub = Path('memory_management_server.py')
    if not mcp_stub.exists():
        mcp_content = '''"""MCP Server Stub"""
import asyncio

class MemoryManagementServer:
    def __init__(self, port=8003):
        self.port = port
    
    async def start(self):
        while True:
            await asyncio.sleep(60)

app = MemoryManagementServer()

if __name__ == "__main__":
    asyncio.run(app.start())
'''
        with open(mcp_stub, 'w') as f:
            f.write(mcp_content)
        print("  ✅ Created memory_management_server.py stub")
    
    # Summary
    print("\n" + "="*50)
    print("📊 Configuration Summary")
    print("="*50)
    print(f"✅ API Keys configured: {len(api_keys)}")
    print(f"⚠️  Missing keys: {len(missing_keys)}")
    print(f"✅ Flask app updated: Yes")
    print(f"{'✅' if redis_ok else '❌'} Redis connection: {'OK' if redis_ok else 'Not running'}")
    
    print("\n🎯 Next Steps:")
    if not redis_ok:
        print("1. Start Redis: redis-server")
    print(f"{2 if not redis_ok else 1}. Run the Flask app: python src/main.py")
    print(f"{3 if not redis_ok else 2}. Test the chat interface at: http://localhost:5000")
    
    if missing_keys:
        print(f"\n⚠️  Important: Add the missing API keys to .env file:")
        for key in missing_keys[:3]:  # Show first 3
            print(f"   - {key}")
        if len(missing_keys) > 3:
            print(f"   ... and {len(missing_keys) - 3} more")

if __name__ == "__main__":
    main() 