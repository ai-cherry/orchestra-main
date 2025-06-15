#!/usr/bin/env python3
"""
Orchestra AI - Secure API Key Setup Helper
Helps configure API keys securely with encryption
"""

import os
import sys
import getpass
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from security.enhanced_secret_manager import EnhancedSecretManager

class APIKeySetup:
    """Helper to set up API keys securely"""
    
    def __init__(self):
        self.secret_manager = EnhancedSecretManager()
        self.required_keys = {
            "LAMBDA_API_KEY": {
                "name": "Lambda Labs API Key",
                "description": "Required for infrastructure provisioning",
                "url": "https://cloud.lambdalabs.com/api-keys",
                "example": "secret_xxxxxxxxxxxxxxxxxxxxx"
            },
            "GITHUB_TOKEN": {
                "name": "GitHub Personal Access Token",
                "description": "Required for repository access and deployment",
                "url": "https://github.com/settings/tokens",
                "example": "ghp_xxxxxxxxxxxxxxxxxxxx",
                "scopes": ["repo", "workflow", "packages"]
            },
            "VERCEL_TOKEN": {
                "name": "Vercel Access Token",
                "description": "Required for frontend deployment",
                "url": "https://vercel.com/account/tokens",
                "example": "xxxxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "OPENAI_API_KEY": {
                "name": "OpenAI API Key",
                "description": "Required for AI capabilities",
                "url": "https://platform.openai.com/api-keys",
                "example": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "PORTKEY_API_KEY": {
                "name": "Portkey API Key",
                "description": "Optional - For AI routing and monitoring",
                "url": "https://app.portkey.ai/api-keys",
                "example": "pk-xxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        }
        
        self.optional_keys = {
            "ANTHROPIC_API_KEY": {
                "name": "Anthropic API Key",
                "description": "Optional - For Claude models",
                "url": "https://console.anthropic.com/api-keys",
                "example": "sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "PINECONE_API_KEY": {
                "name": "Pinecone API Key", 
                "description": "Optional - For vector database",
                "url": "https://app.pinecone.io/",
                "example": "xxxxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "WEAVIATE_API_KEY": {
                "name": "Weaviate API Key",
                "description": "Optional - For vector search",
                "url": "https://console.weaviate.cloud/",
                "example": "xxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        }
    
    def check_current_status(self):
        """Check current API key status"""
        print("🔍 Checking Current API Key Status...")
        print("=" * 50)
        
        configured = []
        missing = []
        
        for key in self.required_keys:
            value = self.secret_manager.get_secret(key)
            if value:
                configured.append(key)
                print(f"✅ {key}: Configured")
            else:
                missing.append(key)
                print(f"❌ {key}: Not configured")
        
        print(f"\nConfigured: {len(configured)}/{len(self.required_keys)} required keys")
        return missing
    
    def setup_key(self, key_name: str, key_info: Dict):
        """Set up a single API key"""
        print(f"\n📝 Setting up {key_info['name']}")
        print(f"   {key_info['description']}")
        print(f"   Get your key at: {key_info['url']}")
        print(f"   Example format: {key_info['example']}")
        
        if 'scopes' in key_info:
            print(f"   Required scopes: {', '.join(key_info['scopes'])}")
        
        # Check if already exists
        existing = self.secret_manager.get_secret(key_name)
        if existing:
            response = input(f"\n   Key already exists. Replace? (y/N): ")
            if response.lower() != 'y':
                print("   Skipped")
                return
        
        # Get new value
        value = getpass.getpass(f"\n   Enter {key_name}: ")
        
        if not value:
            print("   Skipped (no value entered)")
            return
        
        # Validate format (basic check)
        if 'example' in key_info:
            example_prefix = key_info['example'].split('x')[0]
            if example_prefix and not value.startswith(example_prefix):
                print(f"   ⚠️  Warning: Key doesn't match expected format (should start with '{example_prefix}')")
                response = input("   Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("   Skipped")
                    return
        
        # Store the key
        try:
            self.secret_manager.set_local_secret(key_name, value)
            print(f"   ✅ {key_name} stored securely")
        except Exception as e:
            print(f"   ❌ Failed to store key: {str(e)}")
    
    def setup_env_file(self):
        """Update .env file with API keys"""
        print("\n📄 Updating .env file...")
        
        env_file = Path(".env")
        
        # Read existing content
        existing_lines = []
        if env_file.exists():
            with open(env_file) as f:
                existing_lines = f.readlines()
        
        # Prepare new content
        new_lines = []
        keys_to_add = {}
        
        # Check which keys need to be added
        for key in self.required_keys:
            value = self.secret_manager.get_secret(key)
            if value:
                keys_to_add[key] = value
        
        # Process existing lines
        for line in existing_lines:
            # Skip existing API key lines
            if any(key in line for key in keys_to_add):
                continue
            new_lines.append(line)
        
        # Add API keys section if we have keys to add
        if keys_to_add:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            
            new_lines.append("\n# API Keys (managed by secret manager)\n")
            for key, value in keys_to_add.items():
                new_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        print(f"   ✅ Updated .env with {len(keys_to_add)} API keys")
    
    def test_connections(self):
        """Test API connections after setup"""
        print("\n🧪 Testing API Connections...")
        
        # Use the existing test infrastructure
        os.system("python test_api_connectivity.py")
    
    def run_interactive_setup(self):
        """Run interactive setup process"""
        print("🚀 Orchestra AI - API Key Setup")
        print("=" * 50)
        
        # Check current status
        missing = self.check_current_status()
        
        if not missing:
            print("\n✅ All required API keys are configured!")
            response = input("\nWould you like to reconfigure any keys? (y/N): ")
            if response.lower() != 'y':
                return
            missing = list(self.required_keys.keys())
        
        # Set up missing keys
        print("\n📋 Let's set up the missing API keys...")
        
        for key in missing:
            self.setup_key(key, self.required_keys[key])
        
        # Optional keys
        print("\n📋 Optional API Keys")
        response = input("Would you like to configure optional API keys? (y/N): ")
        
        if response.lower() == 'y':
            for key, info in self.optional_keys.items():
                self.setup_key(key, info)
        
        # Update .env file
        response = input("\nUpdate .env file with configured keys? (Y/n): ")
        if response.lower() != 'n':
            self.setup_env_file()
        
        # Test connections
        response = input("\nTest API connections now? (Y/n): ")
        if response.lower() != 'n':
            self.test_connections()
        
        print("\n✅ API key setup complete!")
        print("\nNext steps:")
        print("1. Verify your API connections with: python test_api_connectivity.py")
        print("2. Deploy infrastructure with: cd pulumi && pulumi up")
        print("3. Start services with: ./start_orchestra.sh")

if __name__ == "__main__":
    setup = APIKeySetup()
    setup.run_interactive_setup() 