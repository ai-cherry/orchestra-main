#!/usr/bin/env python3
"""
GitHub Organization Secrets Manager
Manages secrets for the ai-cherry organization
"""

import os
import requests
import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

class GitHubSecretsManager:
    def __init__(self, github_token):
        self.github_token = github_token
        self.org_name = "ai-cherry"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def get_public_key(self):
        """Get the organization's public key for encrypting secrets"""
        url = f"https://api.github.com/orgs/{self.org_name}/actions/secrets/public-key"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get public key: {response.status_code}")
            print(response.text)
            return None
    
    def encrypt_secret(self, public_key, secret_value):
        """Encrypt a secret using the organization's public key"""
        from nacl import encoding, public
        
        # Convert the public key
        public_key_bytes = base64.b64decode(public_key)
        public_key_obj = public.PublicKey(public_key_bytes)
        
        # Encrypt the secret
        box = public.SealedBox(public_key_obj)
        encrypted = box.encrypt(secret_value.encode('utf-8'))
        
        # Return base64 encoded
        return base64.b64encode(encrypted).decode('utf-8')
    
    def create_or_update_secret(self, secret_name, secret_value):
        """Create or update an organization secret"""
        # Get public key
        public_key_data = self.get_public_key()
        if not public_key_data:
            return False
        
        # Encrypt the secret
        encrypted_value = self.encrypt_secret(public_key_data['key'], secret_value)
        
        # Create/update the secret
        url = f"https://api.github.com/orgs/{self.org_name}/actions/secrets/{secret_name}"
        data = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_data['key_id'],
            "visibility": "all"
        }
        
        response = requests.put(url, headers=self.headers, json=data)
        
        if response.status_code in [201, 204]:
            print(f"✅ Secret '{secret_name}' created/updated successfully")
            return True
        else:
            print(f"❌ Failed to create secret '{secret_name}': {response.status_code}")
            print(response.text)
            return False
    
    def setup_infrastructure_secrets(self):
        """Set up all infrastructure-related secrets"""
        secrets = {
            # Infrastructure servers
            "PRODUCTION_SERVER_IP": "45.32.69.157",
            "DATABASE_SERVER_IP": "45.77.87.106", 
            "STAGING_SERVER_IP": "207.246.108.201",
            "LOAD_BALANCER_IP": "45.63.58.63",
            
            # Database credentials
            "DATABASE_URL": "postgresql://orchestra:OrchAI_DB_2024!@45.77.87.106:5432/orchestra",
            "REDIS_URL": "redis://45.77.87.106:6379",
            "WEAVIATE_URL": "http://45.77.87.106:8080",
            
            # API Keys (use environment variables for actual values)
            "PINECONE_API_KEY": os.getenv('PINECONE_API_KEY', 'your-pinecone-key-here'),
            
            # Monitoring credentials
            "GRAFANA_URL": "http://207.246.108.201:3000",
            "GRAFANA_USERNAME": "admin",
            "GRAFANA_PASSWORD": "OrchAI_Grafana_2024!",
            
            # Application credentials
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "OrchAI_Admin2024!",
            "CHERRY_USERNAME": "cherry", 
            "CHERRY_PASSWORD": "Cherry_AI_2024!",
            "DEMO_USERNAME": "demo",
            "DEMO_PASSWORD": "demo123",
            
            # Infrastructure costs and metadata
            "MONTHLY_COST": "455",
            "TOTAL_SERVERS": "7",
            "INFRASTRUCTURE_TIER": "2"
        }
        
        print("🔐 Setting up infrastructure secrets...")
        success_count = 0
        
        for secret_name, secret_value in secrets.items():
            if self.create_or_update_secret(secret_name, secret_value):
                success_count += 1
        
        print(f"\n✅ Successfully configured {success_count}/{len(secrets)} secrets")
        return success_count == len(secrets)

def main():
    # Use the GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub Personal Access Token:")
        print("export GITHUB_TOKEN=your_token_here")
        return
    
    manager = GitHubSecretsManager(github_token)
    
    print("🔐 GITHUB ORGANIZATION SECRETS SETUP")
    print("=====================================")
    
    # Set up infrastructure secrets
    if manager.setup_infrastructure_secrets():
        print("\n🎉 All secrets configured successfully!")
        print("Your infrastructure credentials are now securely stored in GitHub.")
    else:
        print("\n❌ Some secrets failed to configure. Please check the errors above.")

if __name__ == "__main__":
    main()

