"""
Orchestra AI - Updated Infrastructure with Pulumi Native Secrets
Replaces custom secret manager with Pulumi best practices
"""

import pulumi
import pulumi_command as command
from typing import Dict, Any, Optional
from pathlib import Path

# Import Pulumi native secret management
from pulumi_native_secrets import (
    PulumiNativeSecretManager,
    PulumiESCIntegration,
    get_secret,
    require_secret,
    create_environment_variables
)

class PulumiNativeVercelIntegration:
    """Vercel integration using Pulumi native secret management"""
    
    def __init__(self):
        self.secret_manager = PulumiNativeSecretManager()
        
        # Get secrets using Pulumi native methods
        self.vercel_token = require_secret("vercel_token")
        self.github_token = get_secret("github_token")
        self.lambda_backend_url = get_secret("lambda_backend_url", "http://150.136.94.139:8000")
        
        # Project configuration
        self.project_name = get_secret("project_name", "orchestra-ai")
        self.environment = get_secret("environment", "production")
    
    def create_vercel_project_with_native_secrets(self):
        """Create Vercel project using Pulumi native secret management"""
        
        # Create environment variables using Pulumi outputs
        env_vars = create_environment_variables()
        
        # Note: This would use pulumi-vercel provider when available
        # For now, we'll use command-based deployment with native secrets
        
        deployment_script = self.vercel_token.apply(lambda token: f"""#!/bin/bash
set -e

# Set Vercel token from Pulumi secret
export VERCEL_TOKEN="{token}"

# Build and deploy
cd modern-admin
npm install --legacy-peer-deps
npm run build

# Deploy to Vercel
npx vercel --prod --token {token}

echo "✅ Vercel deployment completed with Pulumi native secrets"
""")
        
        return command.local.Command(
            "vercel-deploy-native-secrets",
            create=deployment_script,
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"]
            )
        )

class PulumiNativeLambdaLabsIntegration:
    """Lambda Labs integration using Pulumi native secret management"""
    
    def __init__(self):
        self.secret_manager = PulumiNativeSecretManager()
        
        # Get secrets using Pulumi native methods
        self.lambda_api_key = require_secret("lambda_api_key")
        self.ssh_private_key = require_secret("ssh_private_key")
        self.ssh_public_key = require_secret("ssh_public_key")
    
    def create_lambda_instance_with_native_secrets(self, instance_name: str, instance_type: str, region: str):
        """Create Lambda Labs instance using Pulumi native secrets"""
        
        # Create instance using native secret management
        instance_creation_script = pulumi.Output.all(
            self.lambda_api_key,
            self.ssh_public_key
        ).apply(lambda args: f"""#!/bin/bash
set -e

API_KEY="{args[0]}"
SSH_PUBLIC_KEY="{args[1]}"

# Create SSH key
curl -X POST https://cloud.lambda.ai/api/v1/ssh-keys \\
  -u $API_KEY: \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "orchestra-deployment-key", "public_key": "'$SSH_PUBLIC_KEY'"}}'

# Launch instance
curl -X POST https://cloud.lambda.ai/api/v1/instance-operations/launch \\
  -u $API_KEY: \\
  -H "Content-Type: application/json" \\
  -d '{{"region_name": "{region}", "instance_type_name": "{instance_type}", "ssh_key_names": ["orchestra-deployment-key"], "name": "{instance_name}"}}'

echo "✅ Lambda Labs instance {instance_name} created with Pulumi native secrets"
""")
        
        return command.local.Command(
            f"lambda-instance-{instance_name}",
            create=instance_creation_script,
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"]
            )
        )
    
    def setup_instance_software_with_native_secrets(self, instance_ip: pulumi.Output[str]):
        """Setup software on Lambda Labs instance using native secrets"""
        
        setup_script = pulumi.Output.all(
            self.ssh_private_key,
            create_environment_variables()
        ).apply(lambda args: f"""#!/bin/bash
set -e

SSH_PRIVATE_KEY="{args[0]}"
ENV_VARS='{args[1]}'

# Create temporary SSH key file
echo "$SSH_PRIVATE_KEY" > /tmp/orchestra_ssh_key
chmod 600 /tmp/orchestra_ssh_key

# Setup instance via SSH
ssh -i /tmp/orchestra_ssh_key -o StrictHostKeyChecking=no ubuntu@{instance_ip} << 'REMOTE_SCRIPT'
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone Orchestra AI
cd /opt
sudo git clone https://github.com/ai-cherry/orchestra-main.git
sudo chown -R ubuntu:ubuntu orchestra-main
cd orchestra-main

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file from Pulumi secrets
echo '$ENV_VARS' > .env

# Start services
python api/main.py &
python mcp_unified_server.py &

echo "✅ Orchestra AI services started with Pulumi native secrets"
REMOTE_SCRIPT

# Cleanup
rm -f /tmp/orchestra_ssh_key
""")
        
        return command.local.Command(
            "setup-lambda-software-native-secrets",
            create=setup_script,
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"]
            )
        )

class PulumiNativeInfrastructure:
    """Complete infrastructure using Pulumi native secret management"""
    
    def __init__(self):
        self.secret_manager = PulumiNativeSecretManager()
        
        # Setup ESC integration if organization is configured
        organization = get_secret("pulumi_organization")
        if organization:
            self.esc_integration = PulumiESCIntegration(
                organization=organization.apply(lambda org: org),
                environment_name="orchestra-production"
            )
        else:
            self.esc_integration = None
    
    def deploy_with_native_secrets(self):
        """Deploy complete infrastructure using Pulumi native secrets"""
        
        resources = {}
        
        # Setup ESC environment if configured
        if self.esc_integration:
            esc_setup = self.esc_integration.setup_esc_environment()
            resources["esc_environment"] = esc_setup
        
        # Deploy Vercel frontend
        vercel_integration = PulumiNativeVercelIntegration()
        vercel_deployment = vercel_integration.create_vercel_project_with_native_secrets()
        resources["vercel_deployment"] = vercel_deployment
        
        # Deploy Lambda Labs backend
        lambda_integration = PulumiNativeLambdaLabsIntegration()
        lambda_instance = lambda_integration.create_lambda_instance_with_native_secrets(
            instance_name="orchestra-api-server",
            instance_type="gpu_1x_a100_sxm4", 
            region="us-east-1"
        )
        resources["lambda_instance"] = lambda_instance
        
        # Setup software on Lambda instance
        # Note: In real deployment, we'd get the IP from the instance creation response
        instance_ip = get_secret("lambda_instance_ip", "150.136.94.139")
        software_setup = lambda_integration.setup_instance_software_with_native_secrets(instance_ip)
        resources["software_setup"] = software_setup
        
        return resources

# Initialize and deploy if running directly
if __name__ == "__main__":
    # Create infrastructure with Pulumi native secrets
    infrastructure = PulumiNativeInfrastructure()
    deployed_resources = infrastructure.deploy_with_native_secrets()
    
    # Export outputs
    for resource_name, resource in deployed_resources.items():
        pulumi.export(f"{resource_name}_status", "configured_with_pulumi_native_secrets")
    
    # Export secret management approach
    pulumi.export("secret_management", "pulumi_native_config_and_esc")
    pulumi.export("encryption", "pulumi_automatic_encryption")
    pulumi.export("secret_providers", ["pulumi_config", "pulumi_esc", "external_providers"])
    
    # Export environment variables (masked for security)
    env_vars = create_environment_variables()
    pulumi.export("environment_configured", env_vars.apply(lambda env: len(env) > 0))
    
    pulumi.log.info("Orchestra AI infrastructure deployed with Pulumi native secret management")

