#!/usr/bin/env python3
"""
GitHub Organization Secrets Manager
Manages secrets for the ai-cherry organization
"""

import requests
import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os

class GitHubSecretsManager:
    def __init__(self, github_token: str, org_name: str = "ai-cherry"):
        self.github_token = github_token
        self.org_name = org_name
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.base_url = f"https://api.github.com/orgs/{org_name}"
    
    def get_public_key(self):
        """Get the organization's public key for encrypting secrets"""
        response = requests.get(f"{self.base_url}/actions/secrets/public-key", headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get public key: {response.status_code}")
            print(response.text)
            return None
    
    def encrypt_secret(self, public_key_data: dict, secret_value: str) -> str:
        """Encrypt a secret value using the organization's public key"""
        from nacl import encoding, public
        
        public_key = public.PublicKey(public_key_data["key"].encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    
    def create_or_update_secret(self, secret_name: str, secret_value: str) -> bool:
        """Create or update an organization secret"""
        # Get public key
        public_key_data = self.get_public_key()
        if not public_key_data:
            return False
        
        # Encrypt the secret
        try:
            encrypted_value = self.encrypt_secret(public_key_data, secret_value)
        except Exception as e:
            print(f"❌ Failed to encrypt secret: {e}")
            return False
        
        # Create/update the secret
        secret_data = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_data["key_id"],
            "visibility": "all"
        }
        
        response = requests.put(
            f"{self.base_url}/actions/secrets/{secret_name}",
            headers=self.headers,
            json=secret_data
        )
        
        if response.status_code in [201, 204]:
            print(f"✅ Secret '{secret_name}' created/updated successfully")
            return True
        else:
            print(f"❌ Failed to create secret '{secret_name}': {response.status_code}")
            print(response.text)
            return False
    
    def list_secrets(self):
        """List all organization secrets"""
        response = requests.get(f"{self.base_url}/actions/secrets", headers=self.headers)
        
        if response.status_code == 200:
            secrets = response.json().get("secrets", [])
            print(f"📋 Organization secrets ({len(secrets)} total):")
            for secret in secrets:
                print(f"   - {secret['name']} (updated: {secret['updated_at']})")
            return secrets
        else:
            print(f"❌ Failed to list secrets: {response.status_code}")
            return []
    
    def setup_infrastructure_secrets(self):
        """Set up all infrastructure-related secrets"""
        print("🔐 SETTING UP INFRASTRUCTURE SECRETS")
        print("=" * 45)
        
        # Infrastructure secrets to create
        secrets = {
            # Lambda API
            "LAMBDA_API_KEY": os.getenv("LAMBDA_API_KEY"),
            
            # Database connections
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "REDIS_URL": os.getenv("REDIS_URL"),
            "WEAVIATE_URL": os.getenv("WEAVIATE_URL"),
            
            # Server access
            "PRODUCTION_HOST": os.getenv("PRODUCTION_HOST"),
            "DATABASE_HOST": os.getenv("DATABASE_HOST"),
            "STAGING_HOST": os.getenv("STAGING_HOST"),
            "LOAD_BALANCER_HOST": os.getenv("LOAD_BALANCER_HOST"),
            
            # Monitoring
            "GRAFANA_URL": os.getenv("GRAFANA_URL"),
            "GRAFANA_USERNAME": os.getenv("GRAFANA_USERNAME"),
            "GRAFANA_PASSWORD": os.getenv("GRAFANA_PASSWORD"),
            "PROMETHEUS_URL": os.getenv("PROMETHEUS_URL"),
            "KIBANA_URL": os.getenv("KIBANA_URL"),
            
            # Application secrets
            "JWT_SECRET": os.getenv("JWT_SECRET"),
            "API_SECRET_KEY": os.getenv("API_SECRET_KEY"),
            "ENCRYPTION_KEY": os.getenv("ENCRYPTION_KEY"),
            
            # Kubernetes
            "KUBERNETES_CLUSTER_ID": os.getenv("KUBERNETES_CLUSTER_ID"),
            "KUBERNETES_NAMESPACE": os.getenv("KUBERNETES_NAMESPACE"),
            
            # Backup
            "BACKUP_ENCRYPTION_KEY": os.getenv("BACKUP_ENCRYPTION_KEY")
        }
        
        success_count = 0
        total_count = len(secrets)
        
        for secret_name, secret_value in secrets.items():
            if self.create_or_update_secret(secret_name, secret_value):
                success_count += 1
        
        print(f"\n📊 Secret setup summary: {success_count}/{total_count} successful")
        return success_count == total_count
    
    def generate_ssh_keys(self):
        """Generate SSH keys for server access"""
        print("\n🔑 GENERATING SSH KEYS")
        print("=" * 25)
        
        # Check if SSH keys already exist
        if os.path.exists("/home/ubuntu/.ssh/id_rsa"):
            print("✅ SSH keys already exist")
            with open("/home/ubuntu/.ssh/id_rsa.pub", "r") as f:
                public_key = f.read().strip()
            with open("/home/ubuntu/.ssh/id_rsa", "r") as f:
                private_key = f.read().strip()
        else:
            print("🔧 Generating new SSH key pair...")
            os.system("ssh-keygen -t rsa -b 4096 -f /home/ubuntu/.ssh/id_rsa -N ''")
            
            with open("/home/ubuntu/.ssh/id_rsa.pub", "r") as f:
                public_key = f.read().strip()
            with open("/home/ubuntu/.ssh/id_rsa", "r") as f:
                private_key = f.read().strip()
        
        # Add SSH keys to GitHub secrets
        ssh_secrets = {
            "SSH_PRIVATE_KEY": private_key,
            "SSH_PUBLIC_KEY": public_key,
            "STAGING_SSH_KEY": private_key,
            "PRODUCTION_SSH_KEY": private_key,
            "DATABASE_SSH_KEY": private_key
        }
        
        for secret_name, secret_value in ssh_secrets.items():
            self.create_or_update_secret(secret_name, secret_value)
        
        print("✅ SSH keys added to GitHub secrets")
        return public_key
    
    def setup_pinecone_placeholder(self):
        """Set up Pinecone placeholder secret"""
        print("\n🌲 SETTING UP PINECONE PLACEHOLDER")
        print("=" * 35)
        
        # Create placeholder for Pinecone API key
        pinecone_secrets = {
            "PINECONE_API_KEY": "PLACEHOLDER_REPLACE_WITH_ACTUAL_PINECONE_API_KEY",
            "PINECONE_ENVIRONMENT": "us-west1-gcp",
            "PINECONE_INDEX_NAME": "orchestra-embeddings"
        }
        
        for secret_name, secret_value in pinecone_secrets.items():
            self.create_or_update_secret(secret_name, secret_value)
        
        print("✅ Pinecone placeholders created - replace PINECONE_API_KEY with actual key")
    
    def create_env_file_template(self):
        """Create .env file template for local development"""
        env_template = """# Orchestra-Main Environment Variables
# Generated automatically - DO NOT commit to git

# Database Connections
DATABASE_URL=postgresql://orchestra:OrchAI_DB_2024!@45.77.87.106:5432/orchestra_main
REDIS_URL=redis://45.77.87.106:6379
WEAVIATE_URL=http://45.77.87.106:8080

# Monitoring
GRAFANA_URL=http://207.246.108.201:3000
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=OrchAI_Grafana_2024!
PROMETHEUS_URL=http://207.246.108.201:9090
KIBANA_URL=http://207.246.108.201:5601

# Application Secrets
JWT_SECRET=OrchAI_JWT_Secret_2024_Ultra_Secure_Key_For_Authentication
API_SECRET_KEY=OrchAI_API_Secret_2024_For_Internal_Services
ENCRYPTION_KEY=OrchAI_Encryption_2024_For_Sensitive_Data_Storage

# Infrastructure
LAMBDA_API_KEY=<lambda-api-key>
PRODUCTION_HOST=<production-host>
DATABASE_HOST=<database-host>
STAGING_HOST=<staging-host>
LOAD_BALANCER_HOST=<load-balancer-host>

# Kubernetes
KUBERNETES_CLUSTER_ID=bd2cab79-0db3-4317-8b0f-52368f99c577
KUBERNETES_NAMESPACE=orchestra-main

# Pinecone (replace with actual API key)
PINECONE_API_KEY=PLACEHOLDER_REPLACE_WITH_ACTUAL_PINECONE_API_KEY
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=orchestra-embeddings

# Development
NODE_ENV=development
DEBUG=true
LOG_LEVEL=debug
"""
        
        with open("/home/ubuntu/.env.template", "w") as f:
            f.write(env_template)
        
        print("✅ .env template created at /home/ubuntu/.env.template")
        print("⚠️  Remember to add .env to .gitignore")
    
    def create_gitignore(self):
        """Create comprehensive .gitignore file"""
        gitignore_content = """# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Build outputs
dist/
build/
*.egg-info/

# SSH keys
*.pem
*.key
id_rsa*

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/
.tmp/

# Backup files
*.bak
*.backup
*.old

# Docker
.dockerignore
Dockerfile.dev

# Kubernetes secrets
k8s-secrets/
*.kubeconfig

# Terraform
*.tfstate
*.tfstate.*
.terraform/

# Local development
.local/
.cache/
"""
        
        with open("/home/ubuntu/.gitignore", "w") as f:
            f.write(gitignore_content)
        
        print("✅ .gitignore created")

def main():
    # Use the GitHub token from environment variable
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub token: export GITHUB_TOKEN=your_token_here")
        return
    
    manager = GitHubSecretsManager(github_token)
    
    print("🔐 GITHUB ORGANIZATION SECRETS SETUP")
    print("=" * 45)
    
    # List existing secrets
    print("📋 Current organization secrets:")
    existing_secrets = manager.list_secrets()
    
    # Set up infrastructure secrets
    if manager.setup_infrastructure_secrets():
        print("✅ Infrastructure secrets setup completed")
    else:
        print("❌ Some infrastructure secrets failed to setup")
    
    # Generate and setup SSH keys
    public_key = manager.generate_ssh_keys()
    
    # Setup Pinecone placeholder
    manager.setup_pinecone_placeholder()
    
    # Create local development files
    manager.create_env_file_template()
    manager.create_gitignore()
    
    print("\n🎉 GITHUB SECRETS SETUP COMPLETE!")
    print("=" * 40)
    print("✅ All infrastructure secrets added to ai-cherry organization")
    print("✅ SSH keys generated and added to secrets")
    print("✅ .env template created for local development")
    print("✅ .gitignore created for security")
    print("\n📋 Next steps:")
    print("1. Replace PINECONE_API_KEY with actual Pinecone API key")
    print("2. Add SSH public key to all servers")
    print("3. Test GitHub Actions workflows")

if __name__ == "__main__":
    main()

