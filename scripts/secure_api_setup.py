#!/usr/bin/env python3
"""
Secure API Setup Script
Sets up API keys securely without exposing them in version control
"""

import os
import tempfile
from pathlib import Path

def create_secure_env():
    """Create secure .env file from provided keys"""
    print("🔐 Setting up API keys securely...")
    
    # Base configuration template
    env_template = """# Orchestra AI Services Configuration - Secure Setup
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestra
POSTGRES_USER=orchestra
POSTGRES_PASSWORD=your_secure_password

# Vector Database
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# AI Services - Production Keys
ANTHROPIC_API_KEY={anthropic_key}
FIGMA_PERSONAL_ACCESS_TOKEN={figma_key}
ELEVEN_LABS_API_KEY={eleven_labs_key}
GROK_AI_API_KEY={grok_key}
MISTRAL_API_KEY={mistral_key}
NOTION_API_KEY={notion_key}
OPENAI_API_KEY={openai_key}
OPENROUTER_API_KEY={openrouter_key}
PERPLEXITY_API_KEY={perplexity_key}
PHANTOM_BUSTER_API_KEY={phantom_key}
PORTKEY_API_KEY={portkey_key}
PORTKEY_CONFIG={portkey_config}

# GitHub Integration (using org secrets)
GITHUB_TOKEN=${{GH_CLASSIC_PAT_TOKEN}}
GITHUB_FINE_GRAINED_TOKEN=${{GH_FINE_GRAINED_TOKEN}}

# Roo Code Configuration
ROO_CODE_MODE=enhanced_integration
ROO_CODE_ENDPOINT=via_openrouter
"""
    
    # Keys will be provided via environment or secure input
    # For this setup, we'll read from environment variables set by the user
    keys = {
        'anthropic_key': os.environ.get('SETUP_ANTHROPIC_KEY', ''),
        'figma_key': os.environ.get('SETUP_FIGMA_KEY', ''),
        'eleven_labs_key': os.environ.get('SETUP_ELEVEN_LABS_KEY', ''),
        'grok_key': os.environ.get('SETUP_GROK_KEY', ''),
        'mistral_key': os.environ.get('SETUP_MISTRAL_KEY', ''),
        'notion_key': os.environ.get('SETUP_NOTION_KEY', ''),
        'openai_key': os.environ.get('SETUP_OPENAI_KEY', ''),
        'openrouter_key': os.environ.get('SETUP_OPENROUTER_KEY', ''),
        'perplexity_key': os.environ.get('SETUP_PERPLEXITY_KEY', ''),
        'phantom_key': os.environ.get('SETUP_PHANTOM_KEY', ''),
        'portkey_key': os.environ.get('SETUP_PORTKEY_KEY', ''),
        'portkey_config': os.environ.get('SETUP_PORTKEY_CONFIG', '')
    }
    
    # Format the environment file
    env_content = env_template.format(**keys)
    
    # Write to .env file
    env_file = Path('.env')
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment file created: {env_file}")
    
    # Ensure .env is in .gitignore
    ensure_gitignore_security()
    
    return len([k for k in keys.values() if k])

def ensure_gitignore_security():
    """Ensure sensitive files are in .gitignore"""
    gitignore_file = Path('.gitignore')
    security_entries = [
        "# Environment variables",
        ".env",
        ".env.*", 
        "*.key",
        "*.pem",
        "secrets/",
        "# API Keys",
        "api_keys.txt",
        "config/secrets.json"
    ]
    
    if gitignore_file.exists():
        content = gitignore_file.read_text()
        additions = []
        for entry in security_entries:
            if entry not in content:
                additions.append(entry)
        
        if additions:
            with open(gitignore_file, 'a') as f:
                f.write('\n' + '\n'.join(additions) + '\n')
            print(f"✅ Added {len(additions)} security entries to .gitignore")
    else:
        with open(gitignore_file, 'w') as f:
            f.write('\n'.join(security_entries) + '\n')
        print("✅ Created .gitignore with security entries")

def verify_setup():
    """Verify the current API setup"""
    print("🔍 Verifying API setup...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Count configured services
    configured_services = []
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                if value.strip() and not value.strip().startswith('${'):
                    configured_services.append(key.strip())
    
    print(f"✅ Found {len(configured_services)} configured services:")
    for service in sorted(configured_services):
        if 'API_KEY' in service or 'TOKEN' in service:
            print(f"  🔑 {service}")
        else:
            print(f"  ⚙️ {service}")
    
    return len(configured_services) > 0

if __name__ == "__main__":
    print("🚀 Secure API Setup")
    print("==================")
    
    if verify_setup():
        print("✅ API services are already configured")
        print("🔐 Keys are stored in .env (not tracked by git)")
        print("🚀 Ready to test AI integrations!")
    else:
        print("⚠️ No API configuration found")
        print("💡 Use environment variables SETUP_*_KEY to configure services")
        print("📖 See AI_SERVICES_CONFIGURATION_GUIDE.md for details") 