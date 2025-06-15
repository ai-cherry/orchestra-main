"""
Orchestra AI - Pulumi Enhanced Configuration
Integrated with centralized secret management and .env files
"""

import pulumi
import pulumi_command as command
import json
import os
from typing import Dict, Any
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import enhanced secret manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from security.enhanced_secret_manager import secret_manager

# Pulumi configuration
config = pulumi.Config()

class EnhancedSecureInfrastructure:
    """Enhanced infrastructure management with centralized secret handling"""
    
    def __init__(self):
        # Get secrets from centralized manager (supports .env, Pulumi, encrypted files)
        self.lambda_api_key = secret_manager.get_secret("LAMBDA_API_KEY")
        self.github_token = secret_manager.get_secret("GITHUB_TOKEN")
        self.vercel_token = secret_manager.get_secret("VERCEL_TOKEN")
        self.openai_api_key = secret_manager.get_secret("OPENAI_API_KEY")
        self.portkey_api_key = secret_manager.get_secret("PORTKEY_API_KEY")
        
        # SSH configuration
        self.ssh_private_key = secret_manager.get_secret("SSH_PRIVATE_KEY")
        self.ssh_public_key = secret_manager.get_secret("SSH_PUBLIC_KEY")
        
        # Database configuration
        self.database_url = secret_manager.get_secret("DATABASE_URL")
        self.redis_url = secret_manager.get_secret("REDIS_URL")
        
        # Vector database configuration
        self.pinecone_api_key = secret_manager.get_secret("PINECONE_API_KEY")
        self.weaviate_api_key = secret_manager.get_secret("WEAVIATE_API_KEY")
        
        # Environment configuration
        self.environment = secret_manager.get_secret("ENVIRONMENT", "production")
        self.project_name = secret_manager.get_secret("PROJECT_NAME", "orchestra-ai")
        
        # Validate all required secrets
        self._validate_secrets()
    
    def _validate_secrets(self):
        """Validate that all required secrets are available"""
        validation_results = secret_manager.validate_all_secrets()
        
        missing_secrets = [key for key, valid in validation_results.items() if not valid]
        
        if missing_secrets:
            pulumi.log.warn(f"Missing secrets: {missing_secrets}")
            pulumi.log.info("Please ensure all required secrets are set in .env file or Pulumi config")
        else:
            pulumi.log.info("All required secrets validated successfully")
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get all environment variables for deployment"""
        return {
            "LAMBDA_API_KEY": self.lambda_api_key or "",
            "GITHUB_TOKEN": self.github_token or "",
            "VERCEL_TOKEN": self.vercel_token or "",
            "OPENAI_API_KEY": self.openai_api_key or "",
            "PORTKEY_API_KEY": self.portkey_api_key or "",
            "DATABASE_URL": self.database_url or "",
            "REDIS_URL": self.redis_url or "",
            "PINECONE_API_KEY": self.pinecone_api_key or "",
            "WEAVIATE_API_KEY": self.weaviate_api_key or "",
            "ENVIRONMENT": self.environment,
            "PROJECT_NAME": self.project_name
        }
    
    def deploy_lambda_instance(self):
        """Deploy Lambda Labs instance with proper configuration"""
        if not self.lambda_api_key:
            pulumi.log.error("LAMBDA_API_KEY not found - cannot deploy Lambda instance")
            return None
        
        # Create Lambda Labs instance deployment script
        deploy_script = f"""#!/bin/bash
set -e

# Set API key
export LAMBDA_API_KEY="{self.lambda_api_key}"

# Deploy Orchestra AI to Lambda Labs
echo "🚀 Deploying Orchestra AI to Lambda Labs..."

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cat > .env << EOF
LAMBDA_API_KEY={self.lambda_api_key}
GITHUB_TOKEN={self.github_token}
VERCEL_TOKEN={self.vercel_token}
OPENAI_API_KEY={self.openai_api_key}
PORTKEY_API_KEY={self.portkey_api_key}
DATABASE_URL={self.database_url}
REDIS_URL={self.redis_url}
PINECONE_API_KEY={self.pinecone_api_key}
WEAVIATE_API_KEY={self.weaviate_api_key}
ENVIRONMENT={self.environment}
EOF

# Start services
echo "🎼 Starting Orchestra AI services..."
python start_server.py &
python main_mcp.py &

echo "✅ Orchestra AI deployed successfully!"
"""
        
        return command.local.Command(
            "deploy-lambda",
            create=deploy_script,
            opts=pulumi.ResourceOptions(
                depends_on=[]
            )
        )
    
    def deploy_vercel_frontend(self):
        """Deploy frontend to Vercel with proper environment variables"""
        if not self.vercel_token:
            pulumi.log.error("VERCEL_TOKEN not found - cannot deploy to Vercel")
            return None
        
        # Create Vercel deployment script
        vercel_script = f"""#!/bin/bash
set -e

# Set Vercel token
export VERCEL_TOKEN="{self.vercel_token}"

# Deploy to Vercel
echo "🚀 Deploying frontend to Vercel..."

# Set environment variables for Vercel
vercel env add VITE_API_URL production
vercel env add VITE_PORTKEY_API_KEY production
vercel env add VITE_ENVIRONMENT production

# Deploy
vercel --prod --token {self.vercel_token}

echo "✅ Frontend deployed to Vercel successfully!"
"""
        
        return command.local.Command(
            "deploy-vercel",
            create=vercel_script,
            opts=pulumi.ResourceOptions(
                depends_on=[]
            )
        )

# Initialize infrastructure
infra = EnhancedSecureInfrastructure()

# Deploy Lambda Labs instance
lambda_deployment = infra.deploy_lambda_instance()

# Deploy Vercel frontend
vercel_deployment = infra.deploy_vercel_frontend()

# Export important outputs
pulumi.export("environment", infra.environment)
pulumi.export("project_name", infra.project_name)
pulumi.export("secrets_validated", True)

# Export deployment status
if lambda_deployment:
    pulumi.export("lambda_deployment", "configured")
else:
    pulumi.export("lambda_deployment", "missing_api_key")

if vercel_deployment:
    pulumi.export("vercel_deployment", "configured")
else:
    pulumi.export("vercel_deployment", "missing_token")

