#!/usr/bin/env python3
"""
Simple API key setup script for AI Orchestration
Works without psycopg2 dependency
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

class SimpleSecretsManager:
    """Simple secrets manager without database dependency"""
    
    def __init__(self):
        self.api_keys = {}
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load API keys from environment"""
        # List of API keys to check
        api_key_names = [
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY', 
            'OPENROUTER_API_KEY',
            'GROK_AI_API_KEY',
            'MISTRAL_API_KEY',
            'PERPLEXITY_API_KEY',
            'ELEVEN_LABS_API_KEY',
            'FIGMA_PERSONAL_ACCESS_TOKEN',
            'NOTION_API_KEY',
            'PORTKEY_API_KEY',
            'PORTKEY_CONFIG',
            'PHANTOM_BUSTER_API_KEY',
            'GITHUB_TOKEN',
            'GH_CLASSIC_PAT_TOKEN',
            'GH_FINE_GRAINED_TOKEN'
        ]
        
        for key in api_key_names:
            value = os.environ.get(key)
            if value:
                self.api_keys[key] = value
    
    def add_api_key(self, key: str, value: str):
        """Add an API key"""
        if value and value.strip():
            self.api_keys[key] = value.strip()
    
    def save_to_env_file(self, filepath: str = '.env'):
        """Save API keys to .env file"""
        with open(filepath, 'w') as f:
            f.write("# AI Orchestration API Keys\n")
            f.write("# DO NOT COMMIT THIS FILE TO GIT\n\n")
            
            # Database configuration (using defaults)
            f.write("# Database Configuration\n")
            f.write("DATABASE_URL=postgresql://orchestra:orchestra@localhost/orchestra\n")
            f.write("POSTGRES_HOST=localhost\n")
            f.write("POSTGRES_PORT=5432\n")
            f.write("POSTGRES_DB=orchestra\n")
            f.write("POSTGRES_USER=orchestra\n")
            f.write("POSTGRES_PASSWORD=orchestra\n\n")
            
            # Weaviate configuration
            f.write("# Weaviate Configuration\n")
            f.write("WEAVIATE_URL=http://localhost:8080\n")
            f.write("WEAVIATE_API_KEY=local-dev-key\n\n")
            
            # API Keys
            f.write("# AI Service API Keys\n")
            for key, value in sorted(self.api_keys.items()):
                f.write(f"{key}={value}\n")
        
        print(f"✓ Saved {len(self.api_keys)} API keys to {filepath}")
    
    def export_to_environment(self):
        """Export keys to current environment"""
        for key, value in self.api_keys.items():
            os.environ[key] = value
        print(f"✓ Exported {len(self.api_keys)} API keys to environment")
    
    def display_status(self):
        """Display configuration status"""
        print("\n=== API Keys Configuration Status ===")
        
        services = {
            'Anthropic Claude': 'ANTHROPIC_API_KEY',
            'OpenAI': 'OPENAI_API_KEY',
            'OpenRouter': 'OPENROUTER_API_KEY',
            'Grok AI': 'GROK_AI_API_KEY',
            'Mistral': 'MISTRAL_API_KEY',
            'Perplexity': 'PERPLEXITY_API_KEY',
            'GitHub': 'GITHUB_TOKEN',
            'Portkey': 'PORTKEY_API_KEY'
        }
        
        configured = 0
        for service, key in services.items():
            if key in self.api_keys:
                print(f"✓ {service}: Configured")
                configured += 1
            else:
                print(f"✗ {service}: Not configured")
        
        print(f"\nTotal services configured: {configured}/{len(services)}")
        return configured > 0

def main():
    """Main setup function"""
    print("=== AI Orchestration API Keys Setup ===\n")
    
    manager = SimpleSecretsManager()
    
    # Add API keys from command line or environment
    if len(sys.argv) > 1:
        # Parse command line arguments
        for arg in sys.argv[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                manager.add_api_key(key, value)
    
    # Save to .env file
    manager.save_to_env_file()
    
    # Export to environment
    manager.export_to_environment()
    
    # Display status
    success = manager.display_status()
    
    print("\n=== Next Steps ===")
    print("1. Add your API keys to the environment:")
    print("   export ANTHROPIC_API_KEY='your-key-here'")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   # etc...")
    print("\n2. Run this script again to save them:")
    print("   python3 scripts/setup_api_keys.py")
    print("\n3. Or add them directly:")
    print("   python3 scripts/setup_api_keys.py ANTHROPIC_API_KEY=sk-ant-...")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())