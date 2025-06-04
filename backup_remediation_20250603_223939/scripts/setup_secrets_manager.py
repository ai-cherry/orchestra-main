# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Manages secrets from GitHub Secrets or local environment"""
        """Load secrets from appropriate source"""
            print("Running in GitHub Actions - using GitHub Secrets")
            self._load_github_secrets()
        else:
            print("Running locally - using local configuration")
            self._load_local_secrets()
    
    def _load_github_secrets(self):
        """Load secrets from GitHub environment variables"""
        """Load secrets from local sources"""
        """Parse DATABASE_URL into individual components"""
            print(f"Error parsing DATABASE_URL: {e}")
            # Set defaults
            self.secrets_cache.update({
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432',
                'POSTGRES_DB': 'cherry_ai',
                'POSTGRES_USER': 'cherry_ai',
                'POSTGRES_PASSWORD': 'cherry_ai'
            })
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value"""
        """Get a required secret value"""
            raise ValueError(f"Required secret '{key}' not found")
        return value
    
    def get_database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def export_to_env(self):
        """Export all secrets to environment variables"""
        """Save secrets to .env file for local development"""
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
            print("✓ Database connection successful")
            return True
        except Exception:

            pass
            print(f"✗ Database connection failed: {e}")
            return False
    
    def setup_database(self):
        """Setup database with proper user and permissions"""
            cur.execute("""
            """
                cur.execute("""
                """
                print("Created 'cherry_ai' user")
            
            # Create cherry_ai database if not exists
            cur.execute("""
            """
                cur.execute("""
                """
                print("Created 'cherry_ai' database")
            
            # Grant all privileges
            cur.execute("""
            """
            print("✓ Database setup complete")
            return True
            
        except Exception:

            
            pass
            print(f"Database setup error: {e}")
            print("You may need to manually create the cherry_ai user and database")
            return False


def main():
    """Main setup function"""
    print("=== AI coordination Secrets Manager ===\n")
    
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