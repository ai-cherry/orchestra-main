"""
Orchestra AI - Pulumi Native Secret Management
Replaces custom secret manager with Pulumi best practices using Config and ESC
"""

import pulumi
import pulumi_command as command
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path

class PulumiNativeSecretManager:
    """Pulumi-native secret management using Config and ESC"""
    
    def __init__(self, stack_name: str = "production"):
        self.config = pulumi.Config()
        self.stack_name = stack_name
        
        # Initialize Pulumi ESC environment if available
        self.esc_environment = self.config.get("esc:environment")
        
    def get_secret(self, key: str, default: Optional[str] = None) -> pulumi.Output[str]:
        """Get secret using Pulumi Config with automatic encryption"""
        try:
            # Try to get as secret first (encrypted)
            secret_value = self.config.get_secret(key)
            if secret_value:
                return secret_value
            
            # Fall back to regular config
            regular_value = self.config.get(key, default)
            if regular_value:
                return pulumi.Output.from_input(regular_value)
            
            # Return default as Output
            return pulumi.Output.from_input(default or "")
            
        except Exception as e:
            pulumi.log.warn(f"Failed to get secret {key}: {str(e)}")
            return pulumi.Output.from_input(default or "")
    
    def require_secret(self, key: str) -> pulumi.Output[str]:
        """Require a secret - will fail if not found"""
        try:
            return self.config.require_secret(key)
        except Exception:
            # Try regular config as fallback
            return pulumi.Output.from_input(self.config.require(key))
    
    def set_secret(self, key: str, value: str, stack_name: Optional[str] = None):
        """Set a secret using Pulumi CLI (for setup scripts)"""
        target_stack = stack_name or self.stack_name
        
        # This would be used in setup scripts, not in Pulumi programs
        set_command = f"pulumi config set --secret {key} '{value}' --stack {target_stack}"
        
        return command.local.Command(
            f"set-secret-{key}",
            create=set_command,
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"]
            )
        )
    
    def get_all_secrets(self) -> Dict[str, pulumi.Output[str]]:
        """Get all required secrets for Orchestra AI"""
        secrets = {}
        
        # Core API Keys
        secrets["lambda_api_key"] = self.get_secret("lambda_api_key")
        secrets["github_token"] = self.get_secret("github_token") 
        secrets["vercel_token"] = self.get_secret("vercel_token")
        
        # AI/ML Service Keys
        secrets["openai_api_key"] = self.get_secret("openai_api_key")
        secrets["portkey_api_key"] = self.get_secret("portkey_api_key")
        secrets["anthropic_api_key"] = self.get_secret("anthropic_api_key")
        
        # Database Configuration
        secrets["database_url"] = self.get_secret("database_url")
        secrets["redis_url"] = self.get_secret("redis_url")
        
        # Vector Database Keys
        secrets["pinecone_api_key"] = self.get_secret("pinecone_api_key")
        secrets["weaviate_api_key"] = self.get_secret("weaviate_api_key")
        
        # Notion Integration
        secrets["notion_api_key"] = self.get_secret("notion_api_key")
        
        # Security Configuration
        secrets["jwt_secret_key"] = self.get_secret("jwt_secret_key")
        secrets["orchestra_master_key"] = self.get_secret("orchestra_master_key")
        
        # SSH Configuration
        secrets["ssh_private_key"] = self.get_secret("ssh_private_key")
        secrets["ssh_public_key"] = self.get_secret("ssh_public_key")
        
        return secrets
    
    def create_environment_variables(self) -> pulumi.Output[Dict[str, str]]:
        """Create environment variables from secrets for deployment"""
        secrets = self.get_all_secrets()
        
        # Convert secrets to environment variables
        def create_env_dict(*args):
            env_vars = {}
            secret_values = args
            secret_keys = list(secrets.keys())
            
            for i, key in enumerate(secret_keys):
                if i < len(secret_values) and secret_values[i]:
                    # Convert to uppercase environment variable name
                    env_key = key.upper()
                    env_vars[env_key] = secret_values[i]
            
            # Add non-secret configuration
            env_vars.update({
                "ENVIRONMENT": self.config.get("environment", "production"),
                "PROJECT_NAME": self.config.get("project_name", "orchestra-ai"),
                "API_HOST": "0.0.0.0",
                "API_PORT": "8000",
                "FRONTEND_PORT": "3000",
                "MCP_PORT": "8003"
            })
            
            return env_vars
        
        # Apply the function to all secret outputs
        return pulumi.Output.all(*secrets.values()).apply(create_env_dict)

class PulumiESCIntegration:
    """Pulumi ESC (Environments, Secrets, Configuration) integration"""
    
    def __init__(self, organization: str, environment_name: str):
        self.organization = organization
        self.environment_name = environment_name
        self.config = pulumi.Config()
    
    def create_esc_environment_definition(self) -> Dict[str, Any]:
        """Create ESC environment definition for Orchestra AI"""
        return {
            "values": {
                # Core API Keys (encrypted)
                "lambda_api_key": {
                    "fn::secret": "${LAMBDA_API_KEY}"
                },
                "github_token": {
                    "fn::secret": "${GITHUB_TOKEN}"
                },
                "vercel_token": {
                    "fn::secret": "${VERCEL_TOKEN}"
                },
                
                # AI/ML Service Keys (encrypted)
                "openai_api_key": {
                    "fn::secret": "${OPENAI_API_KEY}"
                },
                "portkey_api_key": {
                    "fn::secret": "${PORTKEY_API_KEY}"
                },
                "anthropic_api_key": {
                    "fn::secret": "${ANTHROPIC_API_KEY}"
                },
                
                # Database Configuration (encrypted)
                "database_url": {
                    "fn::secret": "${DATABASE_URL}"
                },
                "redis_url": {
                    "fn::secret": "${REDIS_URL}"
                },
                
                # Vector Database Keys (encrypted)
                "pinecone_api_key": {
                    "fn::secret": "${PINECONE_API_KEY}"
                },
                "weaviate_api_key": {
                    "fn::secret": "${WEAVIATE_API_KEY}"
                },
                
                # Notion Integration (encrypted)
                "notion_api_key": {
                    "fn::secret": "${NOTION_API_KEY}"
                },
                
                # Security Configuration (encrypted)
                "jwt_secret_key": {
                    "fn::secret": "${JWT_SECRET_KEY}"
                },
                "orchestra_master_key": {
                    "fn::secret": "${ORCHESTRA_MASTER_KEY}"
                },
                
                # SSH Configuration (encrypted)
                "ssh_private_key": {
                    "fn::secret": "${SSH_PRIVATE_KEY}"
                },
                "ssh_public_key": {
                    "fn::secret": "${SSH_PUBLIC_KEY}"
                },
                
                # Non-secret configuration
                "environment": "production",
                "project_name": "orchestra-ai",
                "api_host": "0.0.0.0",
                "api_port": "8000",
                "frontend_port": "3000",
                "mcp_port": "8003"
            },
            
            # Environment imports (for shared configurations)
            "imports": [
                f"{self.organization}/shared-secrets",
                f"{self.organization}/orchestra-base-config"
            ]
        }
    
    def setup_esc_environment(self) -> command.local.Command:
        """Setup ESC environment using Pulumi CLI"""
        env_definition = self.create_esc_environment_definition()
        env_yaml = json.dumps(env_definition, indent=2)
        
        setup_script = f"""#!/bin/bash
set -e

# Create ESC environment definition file
cat > orchestra-esc-env.yaml << 'EOF'
{env_yaml}
EOF

# Create or update ESC environment
pulumi env init {self.organization}/{self.environment_name} --file orchestra-esc-env.yaml || \\
pulumi env update {self.organization}/{self.environment_name} --file orchestra-esc-env.yaml

# Add environment to current stack
pulumi config env add {self.organization}/{self.environment_name}

echo "✅ ESC environment {self.environment_name} configured successfully"
"""
        
        return command.local.Command(
            "setup-esc-environment",
            create=setup_script,
            opts=pulumi.ResourceOptions(
                additional_secret_outputs=["create"]
            )
        )

class PulumiSecretProviderIntegration:
    """Integration with external secret providers via Pulumi"""
    
    def __init__(self):
        self.config = pulumi.Config()
    
    def setup_aws_secrets_manager(self) -> Optional[command.local.Command]:
        """Setup AWS Secrets Manager integration"""
        aws_region = self.config.get("aws:region")
        if not aws_region:
            return None
        
        setup_script = f"""#!/bin/bash
set -e

# Install AWS Secrets Manager provider
pulumi plugin install resource aws

# Configure AWS provider
pulumi config set aws:region {aws_region}

echo "✅ AWS Secrets Manager integration configured"
"""
        
        return command.local.Command(
            "setup-aws-secrets",
            create=setup_script
        )
    
    def setup_azure_key_vault(self) -> Optional[command.local.Command]:
        """Setup Azure Key Vault integration"""
        azure_location = self.config.get("azure:location")
        if not azure_location:
            return None
        
        setup_script = f"""#!/bin/bash
set -e

# Install Azure provider
pulumi plugin install resource azure-native

# Configure Azure provider
pulumi config set azure-native:location {azure_location}

echo "✅ Azure Key Vault integration configured"
"""
        
        return command.local.Command(
            "setup-azure-keyvault",
            create=setup_script
        )
    
    def setup_hashicorp_vault(self) -> Optional[command.local.Command]:
        """Setup HashiCorp Vault integration"""
        vault_address = self.config.get("vault:address")
        if not vault_address:
            return None
        
        setup_script = f"""#!/bin/bash
set -e

# Install Vault provider
pulumi plugin install resource vault

# Configure Vault provider
pulumi config set vault:address {vault_address}

echo "✅ HashiCorp Vault integration configured"
"""
        
        return command.local.Command(
            "setup-vault",
            create=setup_script
        )

# Global instance for easy access
pulumi_secret_manager = PulumiNativeSecretManager()

# Helper functions for backward compatibility
def get_secret(key: str, default: Optional[str] = None) -> pulumi.Output[str]:
    """Get secret using Pulumi native methods"""
    return pulumi_secret_manager.get_secret(key, default)

def require_secret(key: str) -> pulumi.Output[str]:
    """Require secret using Pulumi native methods"""
    return pulumi_secret_manager.require_secret(key)

def get_all_secrets() -> Dict[str, pulumi.Output[str]]:
    """Get all secrets using Pulumi native methods"""
    return pulumi_secret_manager.get_all_secrets()

def create_environment_variables() -> pulumi.Output[Dict[str, str]]:
    """Create environment variables from Pulumi secrets"""
    return pulumi_secret_manager.create_environment_variables()

# Export main classes
__all__ = [
    "PulumiNativeSecretManager",
    "PulumiESCIntegration", 
    "PulumiSecretProviderIntegration",
    "get_secret",
    "require_secret",
    "get_all_secrets",
    "create_environment_variables"
]

