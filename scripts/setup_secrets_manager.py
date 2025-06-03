#!/usr/bin/env python3
"""
Unified Secrets Manager for AI Orchestration System
Handles both GitHub Secrets (production) and local development
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any
import psycopg2
from urllib.parse import urlparse

class SecretsManager:
    """Manages secrets from GitHub Secrets or local environment"""
    
    def __init__(self):
        self.is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
        self.secrets_cache = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from appropriate source"""
        if self.is_github_actions:
            print("Running in GitHub Actions - using GitHub Secrets")
            self._load_github_secrets()
        else:
            print("Running locally - using local configuration")
            self._load_local_secrets()
    
    def _load_github_secrets(self):
        """Load secrets from GitHub environment variables"""
        # These are injected by GitHub Actions
        secret_keys = [
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 
            'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'WEAVIATE_URL', 'WEAVIATE_API_KEY',
            'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'OPENROUTER_API_KEY',
            'GROK_AI_API_KEY', 'MISTRAL_API_KEY', 'PERPLEXITY_API_KEY',
            'ELEVEN_LABS_API_KEY', 'FIGMA_PERSONAL_ACCESS_TOKEN',
            'NOTION_API_KEY', 'PORTKEY_API_KEY', 'PORTKEY_CONFIG',
            'PHANTOM_BUSTER_API_KEY', 'GITHUB_TOKEN',
            'GH_CLASSIC_PAT_TOKEN', 'GH_FINE_GRAINED_TOKEN'
        ]
        
        for key in secret_keys:
            value = os.environ.get(key)
            if value:
                self.secrets_cache[key] = value
    
    def _load_local_secrets(self):
        """Load secrets from local sources"""
        # First, check /etc/orchestra.env for database config
        if Path('/etc/orchestra.env').exists():
            with open('/etc/orchestra.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'DATABASE_URL':
                            self._parse_database_url(value)
        
        # Load from environment variables (for API keys)
        env_keys = [
            'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'OPENROUTER_API_KEY',
            'GROK_AI_API_KEY', 'MISTRAL_API_KEY', 'PERPLEXITY_API_KEY',
            'ELEVEN_LABS_API_KEY', 'FIGMA_PERSONAL_ACCESS_TOKEN',
            'NOTION_API_KEY', 'PORTKEY_API_KEY', 'PORTKEY_CONFIG',
            'PHANTOM_BUSTER_API_KEY', 'GITHUB_TOKEN',
            'GH_CLASSIC_PAT_TOKEN', 'GH_FINE_GRAINED_TOKEN',
            'WEAVIATE_URL', 'WEAVIATE_API_KEY'
        ]
        
        for key in env_keys:
            value = os.environ.get(key)
            if value:
                self.secrets_cache[key] = value
        
        # Set default Weaviate config if not present
        if 'WEAVIATE_URL' not in self.secrets_cache:
            self.secrets_cache['WEAVIATE_URL'] = 'http://localhost:8080'
        if 'WEAVIATE_API_KEY' not in self.secrets_cache:
            self.secrets_cache['WEAVIATE_API_KEY'] = 'local-dev-key'
    
    def _parse_database_url(self, database_url: str):
        """Parse DATABASE_URL into individual components"""
        try:
            parsed = urlparse(database_url)
            self.secrets_cache['POSTGRES_HOST'] = parsed.hostname or 'localhost'
            self.secrets_cache['POSTGRES_PORT'] = str(parsed.port or 5432)
            self.secrets_cache['POSTGRES_DB'] = parsed.path.lstrip('/') or 'orchestra'
            self.secrets_cache['POSTGRES_USER'] = parsed.username or 'orchestra'
            self.secrets_cache['POSTGRES_PASSWORD'] = parsed.password or 'orchestra'
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
            # Set defaults
            self.secrets_cache.update({
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432',
                'POSTGRES_DB': 'orchestra',
                'POSTGRES_USER': 'orchestra',
                'POSTGRES_PASSWORD': 'orchestra'
            })
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value"""
        return self.secrets_cache.get(key, default)
    
    def get_required(self, key: str) -> str:
        """Get a required secret value"""
        value = self.secrets_cache.get(key)
        if not value:
            raise ValueError(f"Required secret '{key}' not found")
        return value
    
    def get_database_url(self) -> str:
        """Construct database URL from components"""
        host = self.get('POSTGRES_HOST', 'localhost')
        port = self.get('POSTGRES_PORT', '5432')
        db = self.get('POSTGRES_DB', 'orchestra')
        user = self.get('POSTGRES_USER', 'orchestra')
        password = self.get('POSTGRES_PASSWORD', 'orchestra')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def export_to_env(self):
        """Export all secrets to environment variables"""
        for key, value in self.secrets_cache.items():
            os.environ[key] = value
    
    def save_to_env_file(self, filepath: str = '.env'):
        """Save secrets to .env file for local development"""
        with open(filepath, 'w') as f:
            f.write("# Auto-generated environment file\n")
            f.write("# DO NOT COMMIT THIS FILE TO GIT\n\n")
            
            # Database configuration
            f.write("# Database Configuration\n")
            f.write(f"DATABASE_URL={self.get_database_url()}\n")
            for key in ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']:
                if key in self.secrets_cache:
                    f.write(f"{key}={self.secrets_cache[key]}\n")
            
            # AI Service Keys
            f.write("\n# AI Service API Keys\n")
            ai_keys = [
                'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'OPENROUTER_API_KEY',
                'GROK_AI_API_KEY', 'MISTRAL_API_KEY', 'PERPLEXITY_API_KEY'
            ]
            for key in ai_keys:
                if key in self.secrets_cache:
                    f.write(f"{key}={self.secrets_cache[key]}\n")
            
            # Other Service Keys
            f.write("\n# Other Service API Keys\n")
            other_keys = [
                'WEAVIATE_URL', 'WEAVIATE_API_KEY',
                'ELEVEN_LABS_API_KEY', 'FIGMA_PERSONAL_ACCESS_TOKEN',
                'NOTION_API_KEY', 'PORTKEY_API_KEY', 'PORTKEY_CONFIG',
                'PHANTOM_BUSTER_API_KEY'
            ]
            for key in other_keys:
                if key in self.secrets_cache:
                    f.write(f"{key}={self.secrets_cache[key]}\n")
            
            # GitHub Tokens
            f.write("\n# GitHub Tokens\n")
            github_keys = ['GITHUB_TOKEN', 'GH_CLASSIC_PAT_TOKEN', 'GH_FINE_GRAINED_TOKEN']
            for key in github_keys:
                if key in self.secrets_cache:
                    f.write(f"{key}={self.secrets_cache[key]}\n")
        
        print(f"Environment file saved to {filepath}")
    
    def verify_database_connection(self) -> bool:
        """Verify database connection works"""
        try:
            conn = psycopg2.connect(self.get_database_url())
            conn.close()
            print("✓ Database connection successful")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def setup_database(self):
        """Setup database with proper user and permissions"""
        try:
            # Connect as postgres superuser to create orchestra user
            admin_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password='postgres'  # Default postgres password
            )
            admin_conn.autocommit = True
            cur = admin_conn.cursor()
            
            # Create orchestra user if not exists
            cur.execute("""
                SELECT 1 FROM pg_user WHERE usename = 'orchestra'
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE USER orchestra WITH PASSWORD 'orchestra';
                """)
                print("Created 'orchestra' user")
            
            # Create orchestra database if not exists
            cur.execute("""
                SELECT 1 FROM pg_database WHERE datname = 'orchestra'
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE DATABASE orchestra OWNER orchestra;
                """)
                print("Created 'orchestra' database")
            
            # Grant all privileges
            cur.execute("""
                GRANT ALL PRIVILEGES ON DATABASE orchestra TO orchestra;
            """)
            
            cur.close()
            admin_conn.close()
            
            print("✓ Database setup complete")
            return True
            
        except Exception as e:
            print(f"Database setup error: {e}")
            print("You may need to manually create the orchestra user and database")
            return False


def main():
    """Main setup function"""
    print("=== AI Orchestration Secrets Manager ===\n")
    
    manager = SecretsManager()
    
    # Export to environment
    manager.export_to_env()
    
    # Save to .env file for local development
    if not manager.is_github_actions:
        manager.save_to_env_file()
        
        # Setup database if needed
        if not manager.verify_database_connection():
            print("\nAttempting to setup database...")
            manager.setup_database()
            manager.verify_database_connection()
    
    # Display summary
    print("\n=== Configuration Summary ===")
    print(f"Environment: {'GitHub Actions' if manager.is_github_actions else 'Local Development'}")
    print(f"Database URL: {manager.get_database_url()}")
    print(f"Weaviate URL: {manager.get('WEAVIATE_URL')}")
    
    # Check which AI services are configured
    print("\n=== AI Services Status ===")
    ai_services = {
        'Anthropic Claude': 'ANTHROPIC_API_KEY',
        'OpenAI': 'OPENAI_API_KEY',
        'OpenRouter': 'OPENROUTER_API_KEY',
        'Grok AI': 'GROK_AI_API_KEY',
        'Mistral': 'MISTRAL_API_KEY',
        'Perplexity': 'PERPLEXITY_API_KEY'
    }
    
    configured_count = 0
    for service, key in ai_services.items():
        if manager.get(key):
            print(f"✓ {service}: Configured")
            configured_count += 1
        else:
            print(f"✗ {service}: Not configured")
    
    print(f"\nTotal AI services configured: {configured_count}/{len(ai_services)}")
    
    return 0 if configured_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())